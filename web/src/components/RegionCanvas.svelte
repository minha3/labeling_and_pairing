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
  let canvas;
  let labels;
  let clickedLabelType;

  function drawRegion(region_) {
    if (region_ !== undefined) {
      const img = new Image();
      img.src = server.get_image_url(region_.image_id);
      img.onload = function () {
        const width = img.naturalWidth;
        const height = img.naturalHeight;
        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);

        const x1 = width * region_.rx1;
        const y1 = height * region_.ry1;
        const x2 = width * region_.rx2;
        const y2 = height * region_.ry2;
        ctx.strokeRect(x1, y1, (x2-x1), (y2-y1));
      }
    }
    else {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      canvas.width = 0;
      canvas.height = 0;
      ctx.beginPath();
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

  $: drawRegion(region)
  $: joinLabels(region, ", ")

</script>
{#if region}
  <canvas bind:this={canvas} style="display: flex; width: 100%;"></canvas>
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
{/if}