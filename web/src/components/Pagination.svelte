<script>
  import { createEventDispatcher, getContext } from "svelte";
  const dispatch = createEventDispatcher();
  const stateContext = getContext('state');

  // 전체 item 수
  export let totalCount = 0;
  // 현재 페이지
  export let pageCurrent = 1;
  // 한 페이지에 포함될 수 있는 최대 item 수
  export let pageSize = 1;
  // 한번에 보여줄 최대 페이지 수
  export let pageStep = 5;
  // 전체 페이지 수
  let pageTotal = 1;
  // 현재 보여줄 시작 페이지 번호
  let pageStart = 1;
  // 현재 보여줄 페이지 수
  let pageCount = 1;

  $: pageStart = Math.floor((pageCurrent-1) / pageStep) * pageStep + 1;
  $: pageTotal = Math.ceil(totalCount / Math.max(1, pageSize))
  $: pageCount = Math.min(pageTotal - pageStart + 1, pageStep);

  function range(size, start=0) {
    return [...Array(size).keys()].map(i => i+start);
  }

  function onClick(e, pageClicked) {
    const state = stateContext.getState();
    const detail = {
      originalEvent: e,
      page: pageClicked,
      pageSize: state.pageSize,
    }
    dispatch("pageChange", detail);

    if (detail.preventDefault !== true)
      stateContext.setPage(pageClicked)
  }
</script>

<nav>
  <ul class="pagination pagination-sm justify-content-center">
    <li class="page-item">
      <button class="btn btn-outline-dark"
              disabled={pageCurrent === 1}
              on:click={e => onClick(e, 1)}>
        처음
      </button>
    </li>
    <li class="page-item">
      <button class="btn btn-outline-dark"
              disabled={pageCurrent === 1}
              on:click={e => onClick(e, pageCurrent-1)}>
        이전
      </button>
    </li>
    {#each range(pageCount, pageStart) as pageIndex}
      <li class="page-item">
        <button class="btn btn-outline-dark"
                class:active={pageCurrent === pageIndex}
                on:click={e => onClick(e, pageIndex)}>
          {pageIndex}
        </button>
      </li>
    {/each}
    <li class="page-item">
      <button class="btn btn-outline-dark"
              disabled={pageCurrent === pageTotal}
              on:click={e => onClick(e, pageCurrent+1)}>
        다음
      </button>
    </li>
    <li class="page-item">
      <button class="btn btn-outline-dark"
              disabled={pageCurrent === pageTotal}
              on:click={e => onClick(e, pageTotal)}>
        마지막
      </button>
    </li>
  </ul>
</nav>