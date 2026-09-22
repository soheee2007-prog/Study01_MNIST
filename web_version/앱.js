// 앱.js: 손글씨 숫자 인식 웹 앱의 화면 동작입니다.
// 모델(가중치)을 불러온 뒤, 그림판에서 손을 뗄 때마다 전처리 → 추론을 거쳐
// 인식 결과·확신도·상위 3개 후보·0~9 확률 막대를 보여 줍니다(desktop_version/app.py와 같은 기능).
// 모델을 불러오는 동안 그린 그림은 적재가 끝나면 한 번 인식합니다. 외부 라이브러리는 쓰지 않습니다.

import { 그림판 } from "./그림판.js";
import { 모델_불러오기 } from "./모델.js";
import { 전처리 } from "./전처리.js";

// 모듈이 실행되었으므로 file:// 안내문은 숨깁니다.
document.getElementById("안내-file").hidden = true;

const 캔버스 = document.getElementById("그림판");
const 결과_글자 = document.getElementById("결과");
const 확신도_글자 = document.getElementById("확신도");
const 후보_목록 = document.getElementById("후보");
const 막대_영역 = document.getElementById("막대들");
const 지우기_단추 = document.getElementById("지우기");

// 0~9 확률 막대를 만듭니다.
const 막대들 = [];
for (let 숫자 = 0; 숫자 < 10; 숫자++) {
  const 줄 = document.createElement("div");
  줄.className = "막대줄";
  const 이름 = document.createElement("span");
  이름.className = "막대이름";
  이름.textContent = String(숫자);
  const 막대 = document.createElement("div");
  막대.className = "막대";
  const 채움 = document.createElement("div");
  채움.className = "채움";
  막대.appendChild(채움);
  줄.append(이름, 막대);
  막대_영역.appendChild(줄);
  막대들.push(채움);
}

let 모델 = null;          // 적재가 끝나면 { 추론, 평균, 표준편차 }
let 인식_대기 = false;    // 적재 중에 그리기가 끝났으면 true

const 판 = new 그림판(캔버스, { 붓두께: 20, 그리기끝: 인식하기, 지워짐: 화면_초기화 });

function 결과_비우기() {
  결과_글자.textContent = "?";
  후보_목록.replaceChildren();
  for (const 채움 of 막대들) {
    채움.style.width = "0%";
    채움.classList.remove("일위");
  }
}

function 인식하기() {
  if (!모델) {
    인식_대기 = true;   // 적재가 끝나면 인식합니다.
    return;
  }
  const 입력 = 전처리(판.회색조_가져오기(), 판.가로, 판.세로, 모델.평균, 모델.표준편차);
  if (입력 === null) return;
  const 확률 = 모델.추론(입력);

  const 순서 = [...확률.keys()].sort((가, 나) => 확률[나] - 확률[가]);
  const 예측 = 순서[0];
  결과_글자.textContent = String(예측);
  확신도_글자.textContent = `확신도 ${(확률[예측] * 100).toFixed(1)}%`;

  const 줄들 = 순서.slice(0, 3).map((숫자, 순위) => {
    const 줄 = document.createElement("li");
    줄.textContent = `${순위 + 1}위  ${숫자}  ${(확률[숫자] * 100).toFixed(1)}%`;
    return 줄;
  });
  후보_목록.replaceChildren(...줄들);

  막대들.forEach((채움, 숫자) => {
    채움.style.width = `${(확률[숫자] * 100).toFixed(2)}%`;
    채움.classList.toggle("일위", 숫자 === 예측);
  });
}

// 그림을 지운 뒤 결과 화면을 처음 상태로 되돌립니다(오른쪽 클릭으로 지웠을 때도 불림).
function 화면_초기화() {
  인식_대기 = false;
  결과_비우기();
  확신도_글자.textContent = 모델 ? "숫자를 그려 보세요" : "모델을 불러오는 중입니다";
}

function 지우기() {
  if (!판.사용가능) return;
  판.지우기();
  화면_초기화();
}

지우기_단추.addEventListener("click", 지우기);
document.addEventListener("keydown", (이벤트) => {
  if (이벤트.key === "Delete") 지우기();
});

async function 시작() {
  확신도_글자.textContent = "모델을 불러오는 중입니다";
  try {
    const 불러온_모델 = await 모델_불러오기(".");
    모델 = 불러온_모델;
  } catch (오류) {
    판.사용가능 = false;
    캔버스.classList.add("막힘");
    지우기_단추.disabled = true;
    확신도_글자.textContent = `모델을 불러오지 못했습니다: ${오류 && 오류.message ? 오류.message : 오류}`;
    return;
  }
  확신도_글자.textContent = "숫자를 그려 보세요";
  // 적재 중에 그린 그림이 있으면 지금 한 번 인식합니다.
  if (인식_대기 && !판.비었음) 인식하기();
  인식_대기 = false;
}

시작();
