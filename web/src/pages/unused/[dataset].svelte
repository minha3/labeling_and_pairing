<script>
  import {createEventDispatcher, setContext} from "svelte";
  import Server from "../../utils/server";
  import Pagination from "../../components/Pagination.svelte";
  import RegionCanvas from "../../components/RegionCanvas.svelte";
  import LabelFilter from "../../components/LabelFilter.svelte";

  const dispatch = createEventDispatcher();
  const server = new Server();
  export let dataset;
  let statusFilter = {'unused': true};
  let labelFilter = {};
  let page = 1;
  let pageSize = 6;
  let totalCount = 0;
  let regions = [];
  let gridCol = 3;
  let labels = {};

  $: filters = Object.assign({}, statusFilter, labelFilter)
  $: getRegions(filters, page, pageSize)
  $: gridRow = Math.ceil(regions.length / gridCol)
  $: getLabelStatistics(statusFilter)

  async function getRegions(filter_, page_, pageSize_) {
    const response = await server.get_bboxes_from_file(
      dataset, filter_, page_, pageSize_
    );
    page = response.page;
    totalCount = response.total;
    regions = response.items;
    pageSize = response.items_per_page;

    if (page > 1 && regions.length === 0)
      page -= 1
  }

  async function getLabelStatistics(filter) {
    const response = await server.get_label_statistics(dataset, filter);
    labels = sortNestedObjects(response);
  }

  function sortNestedObjects(obj) {
    const result = {};
    for (const [key, nestedObj] of Object.entries(obj)) {
      const entries = Object.entries(nestedObj);
      entries.sort((a, b) => a[0].localeCompare(b[0]));
      result[key] = Object.fromEntries(entries);
    }
    return result;
  }

  function onPageChange(event) {
    page = event.detail.page;
  }

  function onFilterChange(event) {
    labelFilter = event.detail.labelFilter;
    page = 1;
  }

  async function onLabelChange() {
    await getRegions(filters, page, pageSize);
    await getLabelStatistics(statusFilter);
  }

  setContext("state", {
    getState: () => ({
      page,
      pageSize,
      labelFilter,
      regions,
    }),
    setPage: (_page) => {
      page = _page;
    },
    setRows: (_rows) => {
      regions = _rows
    },
    setLabelFilter: (_filter) => {
      labelFilter = _filter;
    },
  })
</script>
<div class="container-fluid">
  <div class="row">
    <div class="col-3">
      <LabelFilter labelStatistics={labels} on:filterChange={onFilterChange}/>
    </div>
    <div class="col-9">
      {#each [...Array(gridRow).keys()] as r}
        <div class="row mt-2">
          {#each [...Array(gridCol).keys()] as c}
            <div class="col">
              {#if gridCol * r + c < regions.length}
                <RegionCanvas region={regions[gridCol * r + c]} editCallback={onLabelChange}
                              useEditable={true} />
              {/if}
            </div>
          {/each}
        </div>
      {/each}
      <slot name="bottom">
        <div class="mt-2">
          <Pagination totalCount={totalCount} pageCurrent={page} pageSize={pageSize} on:pageChange={onPageChange}/>
        </div>
      </slot>
    </div>
  </div>
</div>
