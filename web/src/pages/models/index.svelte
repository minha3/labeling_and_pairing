<script>
  import {onMount} from "svelte";
  import Server from "../../utils/server";
  import {formatDate} from "../../utils/util"
  const server = new Server()
  let models = [];

  async function getModels() {
    models = await server.get_models();
    models.sort((a, b) => (a.created_at < b.created_at) ? 1: -1);
  }

  onMount(() => {
    getModels();
  })
</script>
<div style="margin-top: 10px;">
  <table class="table">
    <thead class="thead-light">
    <tr>
      <th scope="col">파일</th>
      <th scope="col">모델</th>
      <th scope="col">버전</th>
      <th scope="col">상태</th>
      <th scope="col">등록일</th>
      <th scope="col">도구</th>
    </tr>
    </thead>
    <tbody>
    {#each models as model}
      <tr>
        <td>{model.filename}</td>
        <td>{model.model}</td>
        <td>{model.version}</td>
        <td>{model.status}</td>
        <td>{formatDate(model.created_at)}</td>
        <td>{model.experiment_tracker}</td>
      </tr>
    {/each}
    </tbody>
  </table>
</div>