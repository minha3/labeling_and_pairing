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
    allRegions = await server.get_bboxes_from_file(dataset, {'unused': false, 'reviewed': false});
  }

  function getTargetRegions(event, target) {
    // when filter condition changed, go to first page of grid
    if (event === 'check') {
      cursorGrid.start = 0;
    }
    filteredRegions = target;
  }

  async function deleteRegions(selectedIndexes) {
    const promises = [];
    for (const i of selectedIndexes) {
      filteredRegions[i].use = false;
      promises.push(server.update_region(filteredRegions[i].id, filteredRegions[i]));
    }
    await Promise.all(promises)
    await getRegions();
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
        <RegionGrid regions={filteredRegions} editCallback={getRegions}
                    labelEditable={true} reviewedEditable={true} useEditable={true}
                    page="label" cursor={cursorGrid} />
    </div>
  </div>
</div>
