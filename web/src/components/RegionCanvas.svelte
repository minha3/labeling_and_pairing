<script>
  import Server from "../utils/server";

  import { createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher();

  const server = new Server()
  const deepCopy = (obj) => JSON.parse(JSON.stringify(obj));

  export let region;
  export let bboxEditable = false;
  let imgCanvas;
  let bboxCanvas;
  let bbox = {'x1': null, 'x2': null, 'y1': null, 'y2': null};

  // to draw the corners of the bounding box prominently
  let boxCornerSize = 8;
  let isDragging = false;
  // to track the client's coordinates when attempting to move the bounding box
  let startCoords = {'x': null, 'y': null};

  $: if (region) drawRegion(region)

  function drawRegion(region_) {
    if (region_ !== undefined) {
      const img = new Image();
      img.src = server.get_image_url(region_.image_id);
      img.onload = function () {
        // initialize the canvas size to fit the image size
        initCanvasSize(img)

        // draw an image just once
        drawImage(img);

        // initialize bbox coordinates
        initBBoxCoords(region_);

        // draw a bbox
        drawBBox();

        // to allow the user to modify the coordinates of the bounding box
        if (bboxEditable)
          addBBoxEventListener();
      }
    }
    else {
      clearCanvas(imgCanvas);
      clearCanvas(bboxCanvas);
    }
  }

  function initCanvasSize(image) {
    const width = image.naturalWidth;
    const height = image.naturalHeight;
    imgCanvas.width = width;
    imgCanvas.height = height;
    // Set the position and size of the bboxCanvas to match the imageCanvas
    bboxCanvas.style.top = 0;
    bboxCanvas.style.left = 0;
    bboxCanvas.width = imgCanvas.width;
    bboxCanvas.height = imgCanvas.height;
  }

  function initBBoxCoords(region_) {
    bbox.x1 = imgCanvas.width * region_.rx1;
    bbox.y1 = imgCanvas.height * region_.ry1;
    bbox.x2 = imgCanvas.width * region_.rx2;
    bbox.y2 = imgCanvas.height * region_.ry2;
  }

  function drawImage(image) {
    const ctx = imgCanvas.getContext('2d');
    ctx.clearRect(0, 0, imgCanvas.width, imgCanvas.width);
    ctx.drawImage(image, 0, 0);
  }

  function drawBBox() {
    const ctx = bboxCanvas.getContext('2d');

    ctx.clearRect(0, 0, bboxCanvas.width, bboxCanvas.width);

    const width = bbox.x2 - bbox.x1;
    const height = bbox.y2 - bbox.y1;
    const corners = [
      {x: bbox.x1, y: bbox.y1},
      {x: bbox.x2, y: bbox.y1},
      {x: bbox.x1, y: bbox.y2},
      {x: bbox.x2, y: bbox.y2},
    ]

    // draw a border of rect
    ctx.strokeStyle = 'black';
    ctx.lineWidth = 3;
    ctx.strokeRect(bbox.x1, bbox.y1, width, height);

    // draw a rect
    ctx.strokeStyle = 'lime';
    ctx.lineWidth = 1;
    ctx.strokeRect(bbox.x1, bbox.y1, width, height);

    // draw a border of corner of rect
    let cornerSize = boxCornerSize;
    let halfCornerSize = cornerSize / 2;

    ctx.fillStyle = 'black';
    for (const corner of corners) {
      ctx.fillRect(corner.x - halfCornerSize, corner.y - halfCornerSize, cornerSize, cornerSize);
    }

    // draw a corner of rect
    cornerSize -= 2;
    halfCornerSize = cornerSize / 2;

    ctx.fillStyle = 'red';
    for (const corner of corners) {
      ctx.fillRect(corner.x - halfCornerSize, corner.y - halfCornerSize, cornerSize, cornerSize);
    }
  }

  function addBBoxEventListener() {
    // to detect when the user wants to change the coordinates of the bounding box
    bboxCanvas.addEventListener('mousedown', (event) => {
      initDragParams();

      const coords = calcClickedCoords(event, bboxCanvas);

      // If the current clicked corner coordinates are within the bounding box coordinate range,
      // update the bounding box coordinates
      updateBBoxCoords(coords.x, coords.y);
    });

    // to update the coordinates of the bounding box and redraw it
    bboxCanvas.addEventListener('mousemove', (event) => {
      if (!isDragging) return;

      const coords = calcClickedCoords(event, bboxCanvas)

      // If the current clicked corner coordinates are within the bounding box coordinate range,
      // update the bounding box coordinates
      updateBBoxCoords(coords.x, coords.y);
      drawBBox();
    });

    bboxCanvas.addEventListener('mouseup', (event) => {
      if (isDragging) {
        initDragParams();
        drawBBox(); // 캔버스를 다시 그리는 함수
        onChange(event);
      }
    })
  }

  function clearCanvas(canvas) {
    const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      canvas.width = 0;
      canvas.height = 0;
      ctx.beginPath();
  }

  function initDragParams() {
    startCoords.x = null;
    startCoords.y = null;
    isDragging = false;
  }

  function calcClickedCoords(event, canvas) {
    // This function converts the viewport coordinates from the mouse event to the
    // corresponding coordinates on the canvas, taking into account any differences
    // between the canvas's logical size and its displayed (viewport) size. This
    // helps to ensure that the coordinates are accurate and consistent, even if
    // there are differences due to CSS styling or other factors.
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;

    return {x, y};
  }

  function updateBBoxCoords(clickedX, clickedY) {
    // 꼭지점 이동을 감지하기 위한 임계치
    const cornerThreshold = boxCornerSize; // 픽셀 단위
    // 바운딩 박스 이동을 감지하기 위한 임계치
    const bboxThreshold = cornerThreshold * 2;

    if (Math.abs(bbox.x1 - clickedX) <= cornerThreshold) {
      bbox.x1 = clickedX;
      isDragging = true;
    }
    else if (Math.abs(bbox.x2 - clickedX) <= cornerThreshold) {
      bbox.x2 = clickedX;
      isDragging = true;
    }

    if (Math.abs(bbox.y1 - clickedY) <= cornerThreshold) {
      bbox.y1 = clickedY;
      isDragging = true;
    }
    else if (Math.abs(bbox.y2 - clickedY) <= cornerThreshold) {
      bbox.y2 = clickedY;
      isDragging = true;
    }

    if (
      (clickedX - bbox.x1) > bboxThreshold
      && (bbox.x2 - clickedX) > bboxThreshold
      && (clickedY - bbox.y1) > bboxThreshold
      && (bbox.y2 - clickedY) > bboxThreshold
    ) {
      isDragging = true;
      if (!startCoords.x && !startCoords.y) {
        startCoords.x = clickedX;
        startCoords.y = clickedY;
      }
      else {
        const dx = (clickedX - startCoords.x);
        const dy = (clickedY - startCoords.y);
        bbox.x1 += dx;
        bbox.x2 += dx;
        bbox.y1 += dy;
        bbox.y2 += dy;
        startCoords.x = clickedX;
        startCoords.y = clickedY;
      }
    }
  }

  function calcBBoxRelCoords() {
    return {
      'rx1': Math.max(0, Math.min(1.0, bbox.x1 / bboxCanvas.width)),
      'ry1': Math.max(0, Math.min(1.0, bbox.y1 / bboxCanvas.height)),
      'rx2': Math.max(0, Math.min(1.0, bbox.x2 / bboxCanvas.width)),
      'ry2': Math.max(0, Math.min(1.0, bbox.y2 / bboxCanvas.height)),
    }
  }

  function onChange(e) {
    const changedRegion = deepCopy(region)
    Object.assign(changedRegion, calcBBoxRelCoords())

    const detail = {
      originalEvent: e,
      region: changedRegion,
    }

    dispatch("bboxChange", detail)
  }
</script>
{#if region}
  <div class="row mt-2">
    <div class="col">
      <canvas bind:this={imgCanvas} style="width: 100%; z-index: 1;"></canvas>
      <canvas bind:this={bboxCanvas} style="width: 100%; z-index: 2; position: absolute;"></canvas>
    </div>
  </div>
{/if}