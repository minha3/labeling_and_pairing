<script>
  import Dataset from '../pages/datasets/index.svelte';
  import Model from '../pages/models/index.svelte';

  // these are our 'pages' to navigate through
  const navOptions = [
      { page: 'Dataset', component: Dataset },
      { page: 'Model Registry', component: Model },
  ];
  let selectedIdx = 0;
  let selected = navOptions[selectedIdx]; // selected page object


function changeComponent(event) {
    selectedIdx = parseInt(event.target.id);
    selected = navOptions[selectedIdx];
}
</script>
<div class="container">
	<!--app navigation -->
	<ul class="nav nav-tabs">
		{#each navOptions as option, i}
		<li class="nav-item">
			<button class="nav-link p-2 ml-1" class:active={selectedIdx===i} on:click={changeComponent} id={i} role="tab">{option.page}</button>
		</li>
		{/each}
	</ul>
	<!-- content wrapper -->
	<div class="row">
		<div class="col-sm-12">
			<div class="p-2">
				<h1>{selected.page}</h1>
				<!-- this is where our main content is placed -->
				<svelte:component this={selected.component}/>
			</div>
		</div>
	</div>
</div>
