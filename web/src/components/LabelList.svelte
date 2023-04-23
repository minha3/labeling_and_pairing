<script>
  import LabelEditor from "./LabelEditor.svelte";
  import LABELS from "./labels.json";

  import { createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher();
  const deepCopy = (obj) => JSON.parse(JSON.stringify(obj));

  export let region;
  export let labelEditable = false;
  export let useEditable = false;
  export let reviewedEditable = false;
  let labels;
  let clickedLabelType;

  $: if (region) joinLabels(region, ", ")

  function joinLabels(region_, delimiter) {
    const values = Array();
    for (const [key, value] of Object.entries(region_.label)) {
      if (LABELS.hasOwnProperty(key) && value != null) {
        values.push(value)
      }
    }
    labels = values.join(delimiter)
  }

  async function onChange(e, regionId, key, value) {
    if (region.label.hasOwnProperty(key)) {
      const changedRegion = deepCopy(region)
      changedRegion.label[key] = value
      const detail = {
        originalEvent: e,
        region: changedRegion,
      }

      dispatch("labelChange", detail)
    }
  }
</script>
{#if region}
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
        <LabelEditor bind:labelType={clickedLabelType} modalId={region.id} onEdit={onChange}/>
      {:else}
        <p>{labels}</p>
      {/if}
      {#if reviewedEditable}
        <button class="btn btn-sm btn-outline-success"
                on:click={e => {onChange(e, region.id, 'reviewed', !region.label.reviewed)}}>
          {region.label.reviewed? '재태깅' : '완료'}
        </button>
      {/if}
      {#if useEditable}
        <button class="btn btn-sm btn-outline-danger"
                on:click={e => {onChange(e, region.id, 'unused', !region.label.unused)}}>
          {region.label.unused? '복구' : '삭제'}
        </button>
      {/if}
    </div>
  </div>
{/if}