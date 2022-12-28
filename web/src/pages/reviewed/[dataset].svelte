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
    allRegions = await server.get_bboxes_from_file(dataset, {'unused': false, 'reviewed': true});
  }

  function getTargetRegions(event, target) {
    // when filter condition changed, go to first page of grid
    if (event === 'check') {
      cursorGrid.start = 0;
    }
    filteredRegions = target;
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
        <RegionGrid regions={filteredRegions} cursor={cursorGrid} editCallback={getRegions}
                    reviewedEditable={true}/>
    </div>
  </div>
</div>
