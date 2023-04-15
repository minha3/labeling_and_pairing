<script>
  import { createEventDispatcher, getContext } from "svelte";
  const dispatch = createEventDispatcher();
  const stateContext = getContext('state');

  // type 별 element 의 개수를 가지는 객체
  // {'category': {'pants': 2, 'skirt': 3}, ...}
  export let labelStatistics = {};
  // type 별 사용자가 체크한 element 리스트를 가지는 객체
  // {'category': ['pants'], ...}
  let filterConditions = {};

  $: initFilterConditions(labelStatistics);

  function initFilterConditions(labelStatistics_) {
    Object.keys(labelStatistics_).forEach(key => {
      if (!filterConditions.hasOwnProperty(key)) {
        filterConditions[key] = Array()
      }
    })

    Object.keys(filterConditions).forEach(key => {
        filterConditions[key] = filterConditions[key].filter(v => labelStatistics_[key][v] > 0)
      }
    )
  }

  function clearChecked() {
    for (const key in filterConditions) {
      filterConditions[key] = [];
    }
    onChange();
  }

  function checkAll() {
    for (const key in filterConditions) {
      filterConditions[key] = Object.keys(labelStatistics[key]);
    }
    onChange();
  }

  function onChange(e) {
    const detail = {
      originalEvent: e,
      labelFilter: filterConditions,
    }

    dispatch("filterChange", detail);

    if (detail.preventDefault !== true)
      stateContext.setLabelFilter(filterConditions);

  }
</script>

<!--  labelStatistics 가 변경될 때마다 filterConditions[key]의 array가 변경되므로 이 부분을 reload 하여 bind:group을 변경된 array로 재설정 해줘야함.-->
{#key labelStatistics}
  <div class="row mt-3 mb-3">
    <div class="col">
      <button class="btn btn-outline-info" on:click={() => {clearChecked()}}>선택 해제</button>
    </div>
<!--    <div class="col">-->
<!--      <button class="btn btn-outline-info" on:click={() => {checkAll()}}>전체 선택</button>-->
<!--    </div>-->
  </div>
  {#each Object.entries(labelStatistics) as [label_type, label_counts]}
    <h5>{label_type}</h5>
    <div class="row ml-1">
      <div class="col">
        {#each Object.entries(label_counts) as [label_name, label_count]}
          {#if label_count > 0}
            <label>
              <input type=checkbox value={label_name} bind:group={filterConditions[label_type]}
                     on:change={e => {onChange(e)}}/>
              {label_name}({label_count})
            </label>
          {/if}
        {/each}
      </div>
    </div>
  {/each}
{/key}