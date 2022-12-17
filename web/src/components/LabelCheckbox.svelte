<script>
  export let regions;
  export let callback;
  let labels = {};
  let filterConditions = {};
  let labelCount = undefined;

  function getLabelsFromRegions(regions) {
    if (regions !== undefined && regions.length > 0) {
      labels = {};
      labelCount = {};

      regions.forEach((region) => {
        for (const [key, value] of Object.entries(region.labels)) {
          if (value != null) {
            if (!labels.hasOwnProperty(key)) {
              labels[key] = Array()
            }
            if (!labels[key].includes(value)) {
              labels[key].push(value)
            }
            if (!labelCount.hasOwnProperty(key)) {
              labelCount[key] = {}
            }
            if (!labelCount[key].hasOwnProperty(value)) {
              labelCount[key][value] = 1
            }
            else {
              labelCount[key][value] += 1
            }
            if (!filterConditions.hasOwnProperty(key)) {
              filterConditions[key] = Array()
            }
          }
        }
      })

      Object.keys(filterConditions).forEach(key => {
          filterConditions[key] = filterConditions[key].filter(v => labels[key].includes(v))
        }
      )
    }
    getTarget('source changed');
  }

  function getTarget(event_name) {
    if (typeof callback == 'function')
      callback(event_name, getFilteredRegions(regions, filterConditions));
  }

  function getFilteredRegions(regions, labels) {
    const r = [];
    if (regions !== undefined && regions.length > 0) {
      regions.forEach((region) => {
        let isInclude = true
        for (const [key, value] of Object.entries(region.labels)) {
          if (labels.hasOwnProperty(key) && labels[key].length > 0) {
            isInclude = isInclude && (labels[key].includes(value))
          }
          if (!isInclude) {
            break
          }
        }
        if (isInclude) {
          r.push(region)
        }
      })
    }
    return r
  }

  function clearChecked() {
    for (const key in filterConditions) {
      filterConditions[key] = [];
    }
    getTarget('clear');
  }

  function resetChecked() {
    filterConditions = Object.assign([], labels);
    getTarget('reset');
  }

  $: getLabelsFromRegions(regions);
</script>

{#if labels && labelCount && filterConditions}
  <div class="row">
    <div class="col">
      <button class="btn btn-outline-info" on:click={() => {clearChecked()}}>전체 해제</button>
    </div>
    <div class="col">
      <button class="btn btn-outline-info" on:click={() => {resetChecked()}}>전체 선택</button>
    </div>
  </div>
<!--  regions 가 변경될 때마다 filterConditions[key]의 array가 변경되므로 이 부분을 reload 하여 bind:group을 변경된 array로 재설정 해줘야함.-->
  {#key regions}
    {#each Object.entries(labels) as [key, values]}
      <h5>{key}</h5>
      <div class="row">
        {#each values as _value}
          <label>
            <input type=checkbox value={_value} bind:group={filterConditions[key]} on:change={() => {getTarget('check')}}/>
            {_value}({labelCount[key][_value] ? labelCount[key][_value] : 0})
          </label>
        {/each}
      </div>
    {/each}
  {/key}
{/if}