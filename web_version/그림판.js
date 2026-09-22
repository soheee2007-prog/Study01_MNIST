// 그림판.js: 마우스·터치·펜으로 숫자를 그리는 280×280 캔버스입니다.
// Pointer Events로 입력을 받고, desktop_version/app.py처럼 누를 때 원을 찍고 움직일 때 선과 원을 그립니다.
// 흰 바탕에 검은 선으로 그리며, 인식에 쓸 회색조 픽셀(R 채널)을 꺼내 줍니다. 외부 라이브러리는 쓰지 않습니다.

export class 그림판 {
  constructor(캔버스, { 붓두께 = 20, 그리기끝 = () => {}, 지워짐 = () => {} } = {}) {
    this.캔버스 = 캔버스;
    this.붓두께 = 붓두께;
    this.그리기끝 = 그리기끝;
    this.지워짐 = 지워짐;      // 오른쪽 클릭으로 지웠을 때 알림(결과 화면 초기화용)
    this.가로 = 캔버스.width;
    this.세로 = 캔버스.height;
    this.붓 = 캔버스.getContext("2d", { willReadFrequently: true });
    this.사용가능 = true;      // false면 그리기 입력을 받지 않습니다(모델 적재 실패 등).
    this.그린것있음 = false;
    this.현재_포인터 = null;   // 지금 그리고 있는 포인터 id
    this.이전_좌표 = null;
    this.마지막_포인터종류 = "mouse";   // 가장 최근 pointerdown의 pointerType(마우스/터치/펜 구분용)

    this.지우기();

    캔버스.addEventListener("pointerdown", (이벤트) => this.#누름(이벤트));
    캔버스.addEventListener("pointermove", (이벤트) => this.#움직임(이벤트));
    캔버스.addEventListener("pointerup", (이벤트) => this.#뗌(이벤트));
    캔버스.addEventListener("pointercancel", (이벤트) => this.#뗌(이벤트));
    // 오른쪽 클릭: 메뉴 대신 지우기 (app.py의 <Button-3>과 같음).
    // 안드로이드 크롬이나 윈도우 터치·펜에서는 길게 누르면 그리는 도중에도 contextmenu가 발생하는데,
    // 이때는 메뉴만 막고 지우지도 획을 끊지도 않습니다(마우스 오른쪽 클릭일 때만 지웁니다).
    캔버스.addEventListener("contextmenu", (이벤트) => {
      이벤트.preventDefault();
      if (!this.사용가능) return;
      const 종류 = 이벤트.pointerType || this.마지막_포인터종류;
      if (종류 !== "mouse") return;
      this.지우기();
      this.지워짐();
    });
  }

  // 화면 좌표를 캔버스 내부 해상도(280×280) 좌표로 바꿉니다. CSS로 줄어들어 보여도 같은 위치에 그려집니다.
  #좌표(이벤트) {
    const 상자 = this.캔버스.getBoundingClientRect();
    return [
      (이벤트.clientX - 상자.left) * this.가로 / 상자.width,
      (이벤트.clientY - 상자.top) * this.세로 / 상자.height,
    ];
  }

  #점_찍기(x, y) {
    this.붓.beginPath();
    this.붓.arc(x, y, this.붓두께 / 2, 0, Math.PI * 2);
    this.붓.fill();
  }

  #누름(이벤트) {
    this.마지막_포인터종류 = 이벤트.pointerType || "mouse";
    if (!this.사용가능 || 이벤트.button !== 0 || this.현재_포인터 !== null) return;
    이벤트.preventDefault();
    this.현재_포인터 = 이벤트.pointerId;
    try {
      this.캔버스.setPointerCapture(이벤트.pointerId);   // 캔버스 밖으로 나가도 계속 받기
    } catch (오류) {
      // 포인터를 잡을 수 없는 경우(이미 사라진 포인터 등)에도 그리기는 계속합니다.
    }
    const [x, y] = this.#좌표(이벤트);
    this.이전_좌표 = [x, y];
    this.그린것있음 = true;
    this.#점_찍기(x, y);
  }

  #움직임(이벤트) {
    if (이벤트.pointerId !== this.현재_포인터 || !this.이전_좌표) return;
    const [x, y] = this.#좌표(이벤트);
    const [이전_x, 이전_y] = this.이전_좌표;
    this.붓.beginPath();
    this.붓.moveTo(이전_x, 이전_y);
    this.붓.lineTo(x, y);
    this.붓.stroke();
    this.#점_찍기(x, y);   // 선 끝을 둥글게
    this.이전_좌표 = [x, y];
  }

  #뗌(이벤트) {
    if (이벤트.pointerId !== this.현재_포인터) return;
    this.현재_포인터 = null;
    this.이전_좌표 = null;
    this.그리기끝();
  }

  // 흰 바탕으로 다시 칠하고 붓 설정을 되돌립니다.
  지우기() {
    this.붓.fillStyle = "#ffffff";
    this.붓.fillRect(0, 0, this.가로, this.세로);
    this.붓.fillStyle = "#000000";
    this.붓.strokeStyle = "#000000";
    this.붓.lineWidth = this.붓두께;
    this.붓.lineCap = "round";
    this.붓.lineJoin = "round";
    this.그린것있음 = false;
    this.현재_포인터 = null;
    this.이전_좌표 = null;
  }

  // 아무것도 그리지 않았으면 true
  get 비었음() {
    return !this.그린것있음;
  }

  // 회색조 픽셀(가로×세로, 행 우선, 흰색 255·검은색 0)을 돌려줍니다.
  // 흰 바탕을 먼저 칠하므로 R=G=B이고 알파는 255라서 R 채널만 읽습니다.
  회색조_가져오기() {
    const 자료 = this.붓.getImageData(0, 0, this.가로, this.세로).data;
    const 회색조 = new Uint8ClampedArray(this.가로 * this.세로);
    for (let i = 0; i < 회색조.length; i++) 회색조[i] = 자료[i * 4];
    return 회색조;
  }
}
