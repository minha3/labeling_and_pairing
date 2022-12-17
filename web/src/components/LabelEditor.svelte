<script>
  import * as LABELS from './labels.json';
  import {onMount} from "svelte";
  export let labelType = undefined;
  export let modalId = undefined;
  export let onEdit = () => {};

  function sortLabels() {
    for (let key in LABELS) {
      if (LABELS[key].hasOwnProperty('labels')) {
        LABELS[key].labels.sort();
      }
    }
  }

  onMount(() => {
    sortLabels();
  })
</script>
<div class="modal fade" id="LabelEditor{modalId}" tabindex="-1" role="dialog" aria-labelledby="modalTitle" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="modalTitle">{labelType}</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        {#if labelType}
          {#each LABELS[labelType].labels as l}
            <button type="button" class="btn btn-outline-info" data-dismiss="modal" on:click={() => {onEdit(modalId, labelType, l)}}>{l}</button>
          {/each}
        {/if}
      </div>
    </div>
  </div>
</div>