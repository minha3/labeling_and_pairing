<script>
  import { url } from '@sveltech/routify';
  import Server from "../../utils/server";
  const server = new Server()
  let fileInput;
  let fileSelected;
  let fileStats = [];

  function readableFileSize(size) {
    let i = size === 0? 0 : Math.floor( Math.log(size) / Math.log(1024) );
    return (size / Math.pow(1024, i)).toFixed(2) + ' ' + ['B', 'KB', 'MB', 'GB', 'TB'][i];
  }

  async function onFileSelected(e) {
    fileSelected = e.target.files[0];
    await server.create_file(fileSelected);
    await getFileStats();
  }

  async function getFileStats() {
    const response = await server.get_files();
    if (response !== undefined) {
      fileStats = response;
      fileStats.forEach(readableFileStats)
      fileStats.sort((a, b) => (a.id < b.id) ? 1 : -1);
    }
  }

  async function deleteFile(element) {
    await server.delete_file(element.id)
    await getFileStats()
  }

  function readableFileStats(element) {
    element.size = readableFileSize(element.size)
    element.readable_error = element.error == null? "" : element.error
    element.canDelete = (element.cnt_url === -1 || element.cnt_image === 0)
    if (element.cnt_url == null) {
      element.readable_cnt_image = "진행중"
      element.readable_cnt_region = "대기중"
    }
    else if (element.cnt_url === -1) {
      element.readable_cnt_image = "실패"
      element.readable_cnt_region = "진행불가"
    }
    else if (element.cnt_image == null) {
      element.readable_cnt_image = `진행중/${element.cnt_url}`
      element.readable_cnt_region = "대기중"
    }
    else if (element.cnt_image === 0) {
      element.readable_cnt_image = `${element.cnt_image}/${element.cnt_url}`
      element.readable_cnt_region = "진행불가"
    }
    else if (element.cnt_region == null) {
      element.readable_cnt_image = `${element.cnt_image}/${element.cnt_url}`
      element.readable_cnt_region = "진행중"
    }
    else if (element.cnt_region === -1) {
      element.readable_cnt_image = `${element.cnt_image}/${element.cnt_url}`
      element.readable_cnt_region = "진행불가"
    }
    else {
      element.readable_cnt_image = `${element.cnt_image}/${element.cnt_url}`
      element.readable_cnt_region = `${element.cnt_region}`
    }
  }

  getFileStats()
</script>
<div>
  <input style="display: none;"
    accept="text/csv"
    bind:this={fileInput}
    type="file"
    on:change={(e)=>onFileSelected(e)}
  />
  <div class="container">
    <div class="row">
      <div class="col-auto">
        <button class="btn btn-outline-dark"
                on:click={()=>{fileInput.value=null;fileSelected=null;fileInput.click();}}>
          New Upload
        </button>
      </div>
      <div class="col-6">
        {#if fileSelected}
          <b>{fileSelected.name} ({readableFileSize(fileSelected.size)})</b>
        {/if}
      </div>
    </div>
  </div>


</div>
<div style="margin-top: 10px;">
  <table class="table">
    <thead class="thead-light">
    <tr>
      <th scope="col">#</th>
      <th scope="col">등록일</th>
      <th scope="col">이름</th>
      <th scope="col">크기</th>
      <th scope="col">이미지 수</th>
      <th scope="col">영역 수</th>
      <th scope="col">라벨 태깅</th>
      <th scope="col">삭제</th>
      <th scope="col">오류</th>
    </tr>
    </thead>
    <tbody>
    {#each fileStats as filestat, i}
      <tr>
        <th scope="row">{filestat.id}</th>
        <td>{filestat.created_at}</td>
        <td>{filestat.name}</td>
        <td>{filestat.size}</td>
        <td>{filestat.readable_cnt_image}</td>
        <td>{filestat.readable_cnt_region}</td>
        <td><a href="{$url(`/labeling/${filestat.id}`)}" hidden={filestat.canDelete}>시작</a></td>
        <td><button class="btn btn-outline-danger" on:click={deleteFile(filestat)}>삭제</button></td>
        <td>{filestat.readable_error}</td>
      </tr>
    {/each}
    </tbody>
  </table>
</div>