let video;
let resultado;
let canvas, ctx;

//camera web do reconhecimento facial
function startCameraRecognition() {
  video = document.getElementById('video');
  resultado = document.getElementById('resultado');

  // Cria canvas sobre o vídeo para desenhar o retângulo verde
  canvas = document.createElement('canvas');
  canvas.width = video.width;
  canvas.height = video.height;
  canvas.style.position = 'absolute';
  canvas.style.top = video.offsetTop + 'px';
  canvas.style.left = video.offsetLeft + 'px';
  document.body.appendChild(canvas);
  ctx = canvas.getContext('2d');

  //ativação do botão do reconhecimento facial que fica no html
  navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } })
    .then(stream => {
      video.srcObject = stream;
      video.play();
      recognizeLoop();
      const buttons = document.querySelectorAll('button');
      buttons.forEach(btn => btn.style.display = 'none');
    });
}

//captura cada frame do video e das imagens e compara para um resultado mais eficaz
function captureFrame() {
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = video.videoWidth;
  tempCanvas.height = video.videoHeight;
  const tempCtx = tempCanvas.getContext('2d');
  tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
  return tempCanvas.toDataURL('image/jpeg');
}

//deixa o reconhecimento rodando em loop
function recognizeLoop() {
  const imageData = captureFrame();

  fetch('/reconhecer', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ image: imageData })
  })
  .then(response => response.json())
  .then(data => {
    // Limpa o canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (data.length === 0) {
      resultado.textContent = 'Nenhum rosto detectado.';
    } else {
      resultado.textContent = data.map(r => `${r.nome} `).join(', ');

      // Desenhar retângulos verdes ao redor dos rostos
      data.forEach(r => {
        const { top, right, bottom, left } = r.box; // r.box deve vir do backend com coordenadas
        ctx.strokeStyle = 'lime'; // verde
        ctx.lineWidth = 3;
        ctx.strokeRect(left, top, right - left, bottom - top);
      });
    }
  });

  setTimeout(recognizeLoop, 2000);
}
