// 전처리.js: 그림판 회색조 그림을 MNIST와 같은 28×28 입력으로 바꿉니다.
// desktop_version/app.py의 전처리()와 단계별로 똑같이 계산합니다.
// 반전 → 글씨 영역(bbox) 잘라내기 → 비율 유지 20×20 LANCZOS 축소 → 28×28 가운데 붙이기
// → 무게중심을 (14, 14)로 정수 이동 → 학습과 같은 평균·표준편차로 정규화.
// LANCZOS 축소는 Pillow(Resample.c)의 고정소수점 계산을 그대로 옮겨 PIL과 같은 값을 냅니다.
// 외부 라이브러리는 쓰지 않습니다.

const 정밀도_비트 = 22;             // PIL: PRECISION_BITS = 32 - 8 - 2
const 한계 = 2 ** 정밀도_비트;       // 1 << 22 (비트 연산 대신 거듭제곱)

// Python round()와 같은 은행가 반올림: 딱 절반이면 짝수 쪽으로 보냅니다.
function 짝수반올림(x) {
  const 아래 = Math.floor(x);
  const 나머지 = x - 아래;
  if (나머지 > 0.5) return 아래 + 1;
  if (나머지 < 0.5) return 아래;
  return 아래 % 2 === 0 ? 아래 : 아래 + 1;
}

function 싱크(x) {
  if (x === 0) return 1;
  x *= Math.PI;
  return Math.sin(x) / x;
}

function 란초스(x) {
  return (-3 <= x && x < 3) ? 싱크(x) * 싱크(x / 3) : 0;
}

// PIL precompute_coeffs + normalize_coeffs_8bpc: 출력 칸마다 읽을 입력 구간과 정수 계수를 구합니다.
function 계수_계산(입력길이, 출력길이) {
  const 배율 = 입력길이 / 출력길이;
  const 필터배율 = Math.max(배율, 1);
  const 지지 = 3 * 필터배율;
  const 역필터배율 = 1 / 필터배율;   // PIL처럼 나누지 않고 역수를 곱합니다(부동소수점 결과가 달라짐).
  const 목록 = [];
  for (let xx = 0; xx < 출력길이; xx++) {
    const 중심 = (xx + 0.5) * 배율;
    let 시작 = Math.trunc(중심 - 지지 + 0.5);
    if (시작 < 0) 시작 = 0;
    let 끝 = Math.trunc(중심 + 지지 + 0.5);
    if (끝 > 입력길이) 끝 = 입력길이;   // 배열 밖 읽기 방지
    const 실수계수 = [];
    let 합 = 0;
    for (let x = 시작; x < 끝; x++) {
      const w = 란초스((x - 중심 + 0.5) * 역필터배율);
      실수계수.push(w);
      합 += w;
    }
    const 정수계수 = 실수계수.map((w) => {
      const v = (합 !== 0 ? w / 합 : w) * 한계;
      return v < 0 ? Math.trunc(-0.5 + v) : Math.trunc(0.5 + v);
    });
    목록.push({ 시작, 정수계수 });
  }
  return 목록;
}

// PIL clip8: 고정소수점 합을 0~255 정수로 자릅니다.
function 자르기8(합) {
  if (합 >= 한계 * 256) return 255;
  if (합 <= 0) return 0;
  return Math.floor(합 / 한계);
}

// 가로 방향 처리: 줄마다 [시작, 시작+계수개수) 구간을 계수로 더합니다.
function 가로_처리(값, 가로, 세로, 새가로) {
  const 계수 = 계수_계산(가로, 새가로);
  const 출력 = new Uint8Array(새가로 * 세로);
  for (let y = 0; y < 세로; y++) {
    const 줄 = y * 가로;
    for (let xx = 0; xx < 새가로; xx++) {
      const { 시작, 정수계수 } = 계수[xx];
      let 합 = 한계 / 2;             // 2^(정밀도_비트-1): 반올림용
      for (let k = 0; k < 정수계수.length; k++) 합 += 값[줄 + 시작 + k] * 정수계수[k];
      출력[y * 새가로 + xx] = 자르기8(합);
    }
  }
  return 출력;
}

// 세로 방향 처리: 칸마다 [시작, 시작+계수개수) 줄을 계수로 더합니다.
function 세로_처리(값, 가로, 세로, 새세로) {
  const 계수 = 계수_계산(세로, 새세로);
  const 출력 = new Uint8Array(가로 * 새세로);
  for (let yy = 0; yy < 새세로; yy++) {
    const { 시작, 정수계수 } = 계수[yy];
    for (let x = 0; x < 가로; x++) {
      let 합 = 한계 / 2;
      for (let k = 0; k < 정수계수.length; k++) 합 += 값[(시작 + k) * 가로 + x] * 정수계수[k];
      출력[yy * 가로 + x] = 자르기8(합);
    }
  }
  return 출력;
}

// PIL Image.resize((새가로, 새세로), Image.LANCZOS)의 "L" 모드와 같은 결과를 돌려줍니다.
// PIL처럼 보통은 가로 → 세로 순서로 처리하고, 크기가 그대로인 방향은 건너뜁니다.
// 단, Pillow의 Image.resize는 세로가 가로의 100배를 넘고 세로를 줄일 때 세로를 먼저 처리합니다
// (예: 폭 2픽셀, 높이 201픽셀 이상인 세로줄). 중간 결과가 8비트로 잘리므로 순서에 따라 값이 달라집니다.
export function 란초스_축소(값, 가로, 세로, 새가로, 새세로) {
  let 결과 = Uint8Array.from(값.subarray(0, 가로 * 세로));
  if (세로 > 가로 * 100 && 새세로 < 세로) {
    결과 = 세로_처리(결과, 가로, 세로, 새세로);
    if (새가로 !== 가로) 결과 = 가로_처리(결과, 가로, 새세로, 새가로);
    return 결과;
  }
  if (새가로 !== 가로) 결과 = 가로_처리(결과, 가로, 세로, 새가로);
  if (새세로 !== 세로) 결과 = 세로_처리(결과, 새가로, 세로, 새세로);
  return 결과;
}

// 회색조(흰 바탕 255, 검은 글씨 0, 행 우선) 그림을 28×28 정규화 입력으로 바꿉니다.
// 그린 것이 없으면 null을 돌려줍니다.
export function 전처리(회색조, 가로, 세로, 평균, 표준편차) {
  // 1) 반전과 글씨 영역(bbox) 찾기: 0이 아닌 픽셀의 왼·위(포함), 오른·아래(포함 안 함)
  const 반전 = new Uint8Array(가로 * 세로);
  let 왼 = 가로, 위 = 세로, 오른 = 0, 아래 = 0;
  for (let y = 0; y < 세로; y++) {
    for (let x = 0; x < 가로; x++) {
      const v = 255 - 회색조[y * 가로 + x];
      반전[y * 가로 + x] = v;
      if (v !== 0) {
        if (x < 왼) 왼 = x;
        if (x + 1 > 오른) 오른 = x + 1;
        if (y < 위) 위 = y;
        if (y + 1 > 아래) 아래 = y + 1;
      }
    }
  }
  if (오른 === 0) return null;

  // 2) 글씨 영역만 잘라내기
  const w = 오른 - 왼, h = 아래 - 위;
  const 글씨 = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) {
    글씨.set(반전.subarray((위 + y) * 가로 + 왼, (위 + y) * 가로 + 오른), y * w);
  }

  // 3) 비율을 유지하며 긴 쪽을 20픽셀로 줄이기
  const 배율 = 20 / Math.max(w, h);
  const 새w = Math.max(1, 짝수반올림(w * 배율));
  const 새h = Math.max(1, 짝수반올림(h * 배율));
  const 축소 = 란초스_축소(글씨, w, h, 새w, 새h);

  // 4) 28×28 검은 바탕 가운데에 붙이기
  const 바탕 = new Uint8Array(28 * 28);
  const 붙일x = Math.floor((28 - 새w) / 2), 붙일y = Math.floor((28 - 새h) / 2);
  for (let y = 0; y < 새h; y++) {
    for (let x = 0; x < 새w; x++) 바탕[(붙일y + y) * 28 + 붙일x + x] = 축소[y * 새w + x];
  }

  // 5) 무게중심이 (14, 14)에 오도록 정수만큼 이동하기 (범위 밖은 0)
  let 총합 = 0, 합x = 0, 합y = 0;
  for (let y = 0; y < 28; y++) {
    for (let x = 0; x < 28; x++) {
      const v = 바탕[y * 28 + x];
      총합 += v; 합x += x * v; 합y += y * v;
    }
  }
  const 이동x = 짝수반올림(14 - 합x / 총합);
  const 이동y = 짝수반올림(14 - 합y / 총합);

  // 6) 정규화: 파이썬(numpy·torch)처럼 단계마다 float32로 반올림합니다.
  const 평균32 = Math.fround(평균), 표준편차32 = Math.fround(표준편차);
  const 출력 = new Float32Array(784);
  for (let y = 0; y < 28; y++) {
    for (let x = 0; x < 28; x++) {
      const 원y = y - 이동y, 원x = x - 이동x;
      const v = (원y >= 0 && 원y < 28 && 원x >= 0 && 원x < 28) ? 바탕[원y * 28 + 원x] : 0;
      출력[y * 28 + x] = Math.fround(Math.fround(v / 255) - 평균32) / 표준편차32;
    }
  }
  return 출력;
}
