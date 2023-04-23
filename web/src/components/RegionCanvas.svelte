<script>
  import LABELS from './labels.json';
  import Server from "../utils/server";
  import LabelEditor from "./LabelEditor.svelte";

  const server = new Server()
  export let region;
  export let editCallback = undefined;
  export let labelEditable = false;
  export let useEditable = false;
  export let reviewedEditable = false;
  let imgCanvas;
  let bboxCanvas;
  let bbox = {'x1': null, 'x2': null, 'y1': null, 'y2': null};
  let labels;
  let clickedLabelType;

  // to draw the corners of the bounding box prominently
  let boxCornerSize = 8;
  let isDragging = false;
  // to track the client's coordinates when attempting to move the bounding box
  let startCoords = {'x': null, 'y': null};

  $: if (region) drawRegion(region)
  $: joinLabels(region, ", ")

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

  function joinLabels(region_, delimiter) {
    const values = Array();
    for (const [key, value] of Object.entries(region_.label)) {
      if (LABELS.hasOwnProperty(key) && value != null) {
        values.push(value)
      }
    }
    labels = values.join(delimiter)
  }

  async function onEdit(regionId, key, value) {
    if (region.label.hasOwnProperty(key)) {
      region.label[key] = value
      const response = await server.update_label(region.label.id, region.label)
      if (typeof editCallback == 'function')
        editCallback(response, key, value)
    }
  }

</script>
{#if region}
  <div class="row">
    <div class="col">
      <canvas bind:this={imgCanvas} style="width: 100%; z-index: 1;"></canvas>
      <canvas bind:this={bboxCanvas} style="width: 100%; z-index: 2; position: absolute;"></canvas>
    </div>
  </div>
  <div class="row mt-2">
    <div class="col">
      {#if labelEditable}
        {#each Object.entries(region.label) as [key, value]}
          {#if LABELS.hasOwnProperty(key) && value}
            <button type="button" class="btn btn-sm btn-outline-info" data-toggle="modal" data-target="#LabelEditor{region.id}" on:click={() => {clickedLabelType = key;}}>
              {value}
            </button>
          {/if}
        {/each}
        <LabelEditor bind:labelType={clickedLabelType} modalId={region.id} onEdit={onEdit}/>
      {:else}
        <p>{labels}</p>
      {/if}
      {#if reviewedEditable}
        <button class="btn btn-sm btn-outline-success"
                on:click={() => {onEdit(region.id, 'reviewed', !region.label.reviewed)}}>
          {region.label.reviewed? '재태깅' : '완료'}
        </button>
      {/if}
      {#if useEditable}
        <button class="btn btn-sm btn-outline-danger"
                on:click={() => {onEdit(region.id, 'unused', !region.label.unused)}}>
          {region.label.unused? '복구' : '삭제'}
        </button>
      {/if}
    </div>
    </div>
{/if}