document.addEventListener("DOMContentLoaded", () => {
  // Seleciona todos os botões que iniciam reconhecimento
  document.querySelectorAll("[id^='startRecognitionBtn']").forEach(btn => {
    btn.addEventListener("click", () => {
      const num = btn.id.replace("startRecognitionBtn", ""); // ex: "1" ou "2"
      startCameraRecognition(num);
    });
  });
});

function startCameraRecognition(num) {
  const video = document.getElementById(`video${num}`);
  const resultado = document.getElementById(`resultado${num}`);
  const container = document.getElementById(`recognitionContainer${num}`);

  container.style.display = "block";

  // Cria o canvas sobre o vídeo
  const canvas = document.createElement("canvas");
  canvas.width = video.width;
  canvas.height = video.height;
  canvas.style.position = "absolute";
  canvas.style.top = video.offsetTop + "px";
  canvas.style.left = video.offsetLeft + "px";
  container.appendChild(canvas);
  const ctx = canvas.getContext("2d");

  // Ativa a câmera
  navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } })
    .then(stream => {
      video.srcObject = stream;
      video.play();

      // Oculta todos os botões de "Iniciar presença" deste card
      const buttons = container.parentElement.querySelectorAll("button");
      buttons.forEach(b => b.style.display = "none");

      // Inicia o loop de reconhecimento
      recognizeLoop(video, resultado, ctx, canvas);
    })
    .catch(err => {
      console.error("Erro ao acessar a câmera:", err);
      resultado.textContent = "Erro ao acessar a câmera.";
    });
}

function captureFrame(video) {
  const tempCanvas = document.createElement("canvas");
  tempCanvas.width = video.videoWidth;
  tempCanvas.height = video.videoHeight;
  const tempCtx = tempCanvas.getContext("2d");
  tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
  return tempCanvas.toDataURL("image/jpeg");
}

function recognizeLoop(video, resultado, ctx, canvas) {
  const imageData = captureFrame(video);

  fetch("/chamado_professor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: imageData })
  })
    .then(response => response.json())
    .then(data => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (!data || data.length === 0) {
        resultado.textContent = "Nenhum rosto detectado.";
      } else {
        resultado.textContent = data.map(r => `${r.nome}`).join(", ");
      }
    })
    .catch(err => {
    console.error("Erro no reconhecimento:", err);
    });

  setTimeout(() => recognizeLoop(video, resultado, ctx, canvas), 2000);
}
