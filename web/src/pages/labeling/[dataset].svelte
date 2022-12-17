<script>
  import Server from "../../utils/server";
  import LabelCheckbox from "../../components/LabelCheckbox.svelte";
  import RegionGrid from "../../components/RegionGrid.svelte";
  import { onMount } from 'svelte';

  const server = new Server()
  export let dataset;
  let allRegions = [];
  let filteredRegions = [];
  // to load first page of grid when filter condition changed
  let cursorGrid = {'start': 0};

  async function getRegions() {
    allRegions = await server.get_regions_from_file(dataset);
  }

  function getTargetRegions(event, target) {
    // when filter condition changed, go to first page of grid
    if (event === 'check') {
      cursorGrid.start = 0;
    }
    filteredRegions = target;
  }

  async function deleteRegions(selectedIndexes) {
    for (const i of selectedIndexes) {
      filteredRegions[i].use = false;
      await server.update_region(filteredRegions[i].id, filteredRegions[i]);
    }
    await getRegions();
  }

  function onEdit() {
    getRegions();
  }

  function onDelete() {
    getRegions();
  }

  onMount(() => {
    getRegions();
  })


</script>
<div class="container-fluid">
  <div class="row">
    <div class="col-3">
        <LabelCheckbox regions={allRegions} callback={getTargetRegions}/>
    </div>
    <div class="col-9">
        <RegionGrid regions={filteredRegions} editCallback={onEdit} deleteCallback={onDelete}
                    selectCallback={deleteRegions} page="label" cursor={cursorGrid}/>
    </div>
  </div>
</div>
