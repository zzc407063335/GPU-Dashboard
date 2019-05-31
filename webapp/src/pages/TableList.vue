<template>
    <div class="row">
      <div class="col-12">
        <card :title=processTable.title :subTitle=processTable.subTitle>
          <div slot="raw-content" class="table-responsive">
            <paper-table :data="processTable.data" :columns="processTable.columns">
            </paper-table>
          </div>
        </card>
      </div>

    </div>
</template>
<script>
import { PaperTable } from "@/components";
import axios from 'axios'

const tableColumns = ["PID", "进程名", "内存占用", "设备编号"];
const tableData = [
  {
    pid: 1,
    进程名: "python",
    内存占用: "$36.738",
    设备编号: "Niger",
  },
  {
    pid: 2,
    进程名: "python",
    内存占用: "$23,789",
    设备编号: "Curaçao",
  },
  {
    pid: 3,
    进程名: "python",
    内存占用: "$56,142",
    设备编号: "Netherlands",
  },
  {
    pid: 4,
    进程名: "python",
    内存占用: "$38,735",
    设备编号: "Korea, South",
  },
  {
    pid: 5,
    进程名: "python",
    内存占用: "$63,542",
    设备编号: "Malawi",
  }
];

export default {
  components: {
    PaperTable
  },
  data() {
    return {
      processTable: {
        title: "进程查看",
        subTitle: "每个设备运行进程查看",
        columns: [...tableColumns],
        data: [...tableData]
      }
    };
  },
  methods: {
      getData() {
          axios.get('https://api.coindesk.com/v1/bpi/currentprice.json')
          .then(function (response){
            var axisData = (new Date()).toLocaleTimeString().replace(/^\D*/,'');
            console.log(axisData);
            console.log(response);
          })
      },
            // 这是一个定时器
    timer() {
          return setInterval(()=>{
              this.getData()
          },5000)
    }
  },
  mounted() {
      // console.log("加载完成")
  },
  created() {
      // console.log("创建完成")
      // this.getData()
  },
  activated(){
      this.timer_id = this.timer()

      // console.log("重新载入")
  },
  deactivated() {
      // console.log("缓存起来")
      clearInterval(this.timer_id)
  },
  beforeDestroy() {
      // console.log("销毁")
      clearInterval(this.timer_id)
  }
};
</script>
<style>
</style>
