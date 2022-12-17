<script>
  import RegionCanvas from "./RegionCanvas.svelte";
  export let regions = undefined;
  export let id = "RegionList"
  export let deleteCallback = undefined;
  let checkedIds = [];
  let nCol = 5;

  function onDelete() {
    if (typeof deleteCallback == 'function')
      deleteCallback(checkedIds);
    checkedIds = [];
  }
</script>
<div class="modal fade" id={id} tabindex="-1" role="dialog" aria-labelledby="modalTitle" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="modalTitle">{regions.length}개</h5>
        {#if deleteCallback}
          <button class="btn btn-sm btn-outline-danger" data-dismiss="modal" on:click={onDelete}>선택 제외하고 닫기</button>
        {/if}
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        {#if regions}
          {#each [...Array(parseInt(regions.length/nCol)+1).keys()] as i}
            <div class="row">
              {#each [...Array(nCol).keys()] as j}
                {#if i*nCol+j < regions.length}
                  <div class="col">
                    {#if deleteCallback}
                      <input type=checkbox bind:group={checkedIds} value={i*nCol+j} />
                    {/if}
                    <RegionCanvas bind:region={regions[i*nCol+j].region} showLabels={false}/>
                  </div>
                {/if}
              {/each}
            </div>
          {/each}
        {/if}
      </div>
    </div>
  </div>
</div>
