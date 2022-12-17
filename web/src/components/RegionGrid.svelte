<script>
  import RegionCanvas from "./RegionCanvas.svelte";
  import RegionListModal from "./RegionListModal.svelte";
  import Server from "../utils/server";

  const server = new Server();
  export let page = 'pair';
  export let sourceRegion = undefined;
  export let regions = [];
  export let editCallback = undefined;
  export let deleteCallback = undefined;
  export let selectCallback = undefined;
  export let showLabels = true;
  export let cursor = {'start': 0};
  let start = 0;
  let end;
  let total = 6;
  let nRow;
  let nCol = 3;
  let checkState = {}

  $: start = cursor.start;
  $: if (start >= regions.length) start = 0;
  $: end = Math.min(start + total, regions.length)
  $: nRow = Math.ceil((end - start) / nCol)
  $: checkState = {...new Array(regions.length).fill(false)}

  let checkedRegions = [];

  function prev() {
    start = (start === 0 ? Math.floor(regions.length / total) * total : start - total)
  }

  function next() {
    start = (end === regions.length ? 0 : start + total)
  }

  function checkRegion(e) {
    checkState[e.target.value] = e.target.checked
  }

  function uncheckRegion(indexes) {
    for (const index of indexes) {
      checkState[checkedRegions[index].index] = false;
    }
  }

  function showCheckedRegions() {
    checkedRegions = []
    for (const [key, value] of Object.entries(checkState)) {
      if (value) {
        if (page === 'pair') {
          checkedRegions.push({
            'index': key,
            [regions[key].labels.region]: regions[key],
            [sourceRegion.labels.region]: sourceRegion
          })
        }
        else if (page === 'label') {
          checkedRegions.push({
            'index': key,
            'region': regions[key]
          })
        }
      }
    }
  }

  function onEdit() {
    if (typeof editCallback == 'function')
      editCallback();
  }

  function onDelete() {
    if (typeof deleteCallback == 'function')
      deleteCallback();
  }

  function onSelect() {
    let selectedIndexes = [];
    for (const [key, value] of Object.entries(checkState)) {
      if (value) {
        selectedIndexes.push(key)
      }
    }
    if (typeof selectCallback == 'function')
      selectCallback(selectedIndexes);
  }

</script>
<div class="d-flex justify-content-center mt-3 mb-3">
  <button class="btn btn-outline-info mr-1" disabled={start === 0} on:click={prev}>이전</button>
  <button class="btn btn-outline-info ml-1" disabled={end === regions.length} on:click={next}>다음</button>
  {#if selectCallback}
    {#if page === 'label'}
      <button class="btn btn-outline-primary ml-1" data-toggle="modal" data-target="#RegionList" on:click={showCheckedRegions}>선택 보기</button>
      <RegionListModal regions={checkedRegions} deleteCallback={uncheckRegion} id="RegionList"/>
      <button class="btn btn-outline-danger ml-1" on:click={onSelect}>선택 삭제</button>
    {/if}
  {/if}
</div>
{#each [...Array(nRow).keys()] as r}
  <div class="row">
    {#each [...Array(nCol).keys()] as c}
      <div class="col">
        {#if start + nCol * r + c < end}
          {#if selectCallback}
            <input type=checkbox checked={checkState[start + nCol*r + c]} value={start + nCol*r + c} on:change={ e => {checkRegion(e)}}/>
          {/if}
          <RegionCanvas region={regions[start + nCol*r + c]}
                        editCallback={editCallback !== undefined? onEdit: undefined}
                        deleteCallback={deleteCallback !== undefined? onDelete: undefined} showLabels={showLabels}/>
        {/if}
      </div>
    {/each}
  </div>
{/each}
