<template>

    <div>
      <div class="row">
        <div class="col-md-6 col-xl-4">
            <div class="card">
              <div class="card-body">
                <div>
                  <div class="row">
                     <div class="col-5">
                        <div class="icon-big text-center icon-danger">
                          <i :class="'ti-link'"></i>
                        </div>
                     </div>

                     <div class="col-7 text-center">
                       <p-button round outline block @click.native="notifyVue('top','center')"> {{buttonText}} </p-button>
                     </div>
                  </div>
                  <hr>

                  <h4><p class="category"> 当前间隔: {{intervalTime/1000}}s </p></h4>

                  <div class="row">
                    <div class="col-4"><p-button size="sm" round outline block @click.native="notifyVueChangeTime('top','right',5)"> 5s </p-button></div>
                    <div class="col-4"><p-button size="sm" round outline block @click.native="notifyVueChangeTime('top','right',30)"> 30s </p-button></div>
                    <div class="col-4"><p-button size="sm" round outline block @click.native="notifyVueChangeTime('top','right',60)"> 60s </p-button></div>
                  </div>
                </div>

              </div>
            </div>
        </div>
      </div>
      <div class="row">
        <div class="col-md-6 col-12">
            <div class="card">
              <div class="card-header" >
                  <h4 class="card-title">内存使用情况 (GiB)</h4>
              </div>
              <div  class="card-body">
                  <ve-line style="width: auto; height: 350px; position: relative;" :data="memData" :settings="normolChartSettings" :extend="memExtend" :colors="memcolors"></ve-line>
                  <div class="footer">
                    <div class="stats text-center">
                        <span><i class="ti-reload"></i> {{intervalTime/1000}}s 刷新 </span>
                    </div>
                  </div>
              </div>
            </div>
        </div>
        <div class="col-md-6 col-12">
            <div class="card">
              <div class="card-header" >
                  <h4 class="card-title">Bar1内存使用情况 (MiB)</h4>
              </div>
              <div  class="card-body">
                <ve-line style="width: auto; height: 350px; position: relative;" :colors="bar1memcolors" :data="bar1memData" :settings="normolChartSettings" :extend="bar1memExtend"></ve-line>
                <div class="footer">
                  <div class="stats text-center">
                      <span><i class="ti-reload"></i> {{intervalTime/1000}} 刷新 </span>
                  </div>
                </div>
              </div>
            </div>
        </div>
      </div>
      <div class="row">
          <div class="col-12">
            <card :title="'进程查看'" :subTitle="'每个设备运行进程查看'" >
              <div slot="raw-content" class="table-responsive">
                <paper-table :data="tableData" :columns="tablecolumns">

                </paper-table>
              </div>
            </card>
          </div>
      </div>
    </div>
</template>
<script>
import { PaperTable, StatsCard } from "@/components";
import NotificationTemplate from './Notifications/NotificationTemplate';

import VeLine from 'v-charts/lib/line.common'
// const queryURL = "http://train_box:5002/gpuinfo/" //后面要写到配置文件
const queryURL = "/gpuinfo/"
import axios from 'axios'

export default {
  components: {
    VeLine,
    StatsCard,
    PaperTable
  },
  data() {
    this.memcolors= ['#546570','#bda29a','#c4ccd3','#c23531', '#2f4554', '#61a0a8','#d48265',
         '#91c7ae','#749f83','#ca8622','#6e7074'
    ],
    this.bar1memcolors= ['#F08080','#8B7355','#00CED1','#FAEBD7', '#2f4554', '#61a0a8','#d48265',
         '#91c7ae','#749f83','#ca8622','#6e7074'
    ],
    this.normolChartSettings= {
      area: true
    },
    this.memExtend= {
        'yAxis.0.min': 0, // yAxis.0：y轴左侧 //设置纵坐标的最小值
        'yAxis.0.max': 0, // 设置纵坐标的最大值
        'yAxis.0.minInterval': 10, // minInterval设置间隔值，1为整数
        'yAxis.1.splitLine.show': false,// yAxis.1： y轴右侧 //不显示值标线
        'xAxis.0.show': true
    },
    this.bar1memExtend= {
        'yAxis.0.min': 0, // yAxis.0：y轴左侧 //设置纵坐标的最小值
        'yAxis.0.max': 0, // 设置纵坐标的最大值
        'yAxis.0.minInterval': 10, // minInterval设置间隔值，1为整数
        'yAxis.1.splitLine.show': false,// yAxis.1： y轴右侧 //不显示值标线
        'xAxis.0.show': true
    }
    return {
      intervalTime: 30000,
      buttonText: "暂停监测",
      gpuCount: 0,
      bar1memData: {
          columns: ['时间'],
          rows: [
            { '时间': 'NA0'},
            { '时间': 'NA1'},
            { '时间': 'NA2'},
            { '时间': 'NA3'},
            { '时间': 'NA4'},
            { '时间': 'NA5'}
          ]
        },
      memData: {
            columns: ['时间'],
            rows: [
              { '时间': 'NA0'},
              { '时间': 'NA1'},
              { '时间': 'NA2'},
              { '时间': 'NA3'},
              { '时间': 'NA4'},
              { '时间': 'NA5'}
            ]
      },
      tablecolumns: ["PID", "进程名称", "内存占用", "设备编号"],
      tableData: [
      ],
      }
  },
  methods: {
    notifyVueChangeTime(verticalAlign, horizontalAlign, intervalTime) {
        clearInterval(this.timer_id)
        this.timer_id = false
        this.intervalTime = intervalTime * 1000
        this.timer_id = this.timer()
        this.$notify({
          component: NotificationTemplate,
          icon: "ti-drupal",
          horizontalAlign: horizontalAlign,
          verticalAlign: verticalAlign,
          type: "warning"
        });
    },
    notifyVue(verticalAlign, horizontalAlign) {
        if(this.timer_id) {
          this.buttonText="开始监测"
          clearInterval(this.timer_id)
          this.timer_id = false
        } else {
          this.buttonText="暂停监测"
          this.timer_id = this.timer()
        }
        this.$notify({
          component: NotificationTemplate,
          icon: "ti-gift",
          horizontalAlign: horizontalAlign,
          verticalAlign: verticalAlign,
          type: "success"
        });
    },
      async getStaticInfo() {
          var api = "gpu_counts"
          var self = this //指向data内的数据
          await axios.post(queryURL+api,{
          }).then(function (response) {
            self.gpuCount = response.data['counts'] //设备数量
          })
          .catch(function (error) {
            console.log(error)
          })
          for (var i = 0; i < self.gpuCount; i++) {
            api = "gpu_mem"
            await axios.post(queryURL+api,{"gpu_index":i}).then(function (response) {
              self.memExtend['yAxis.0.max'] = Math.ceil(Math.max(self.memExtend['yAxis.0.max'],Number((Number(response.data['mem_total'])).toFixed(2))))
              self.memExtend['yAxis.0.minInterval'] = self.memExtend['yAxis.0.max'] / 10

            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_bar1mem"
            await axios.post(queryURL+api,{"gpu_index":i}).then(function (response) {
              self.bar1memExtend['yAxis.0.max'] = Math.ceil(Math.max(self.bar1memExtend['yAxis.0.max'],Number((Number(response.data['mem_total'])).toFixed(2))))
              self.bar1memExtend['yAxis.0.minInterval'] = self.bar1memExtend['yAxis.0.max'] / 10
            })
            .catch(function (error) {
              console.log(error)
            })

          }

          for (var i = 0; i < self.gpuCount; i++) {
            //初始化列表
            this.bar1memData.columns.push('GPU ' + i.toString())
            this.memData.columns.push('GPU ' + i.toString())
            for (var j = 0; j < self.memData.rows.length; j++) {
                this.memData.rows[j]['GPU ' + i.toString()] = 0
                this.bar1memData.rows[j]['GPU ' + i.toString()] = 0
            }
          }
      },
      async getData() {
        var self = this
        var axisData = (new Date()).toLocaleTimeString().replace(/^\D*/,'')
        var len = this.memData.rows.length
        for (var i = 0; i < len - 1; i++) {
            for (var j = 0; j < self.gpuCount; j++) {
              this.memData.rows[i]['GPU ' + j.toString()] = this.memData.rows[i + 1]['GPU ' + j.toString()]
              this.memData.rows[i]['时间'] = this.memData.rows[i + 1]['时间']
              this.bar1memData.rows[i]['GPU ' + j.toString()] = this.bar1memData.rows[i + 1]['GPU ' + j.toString()]
              this.bar1memData.rows[i]['时间'] = this.bar1memData.rows[i + 1]['时间']
            }
        }
        this.memData.rows[len - 1]['时间'] = axisData
        this.bar1memData.rows[len - 1]['时间'] = axisData

        var api
        var proc_num
        var tmptableData = []

        try{
          for (var i = 0; i < self.gpuCount; i++) {
              api = "gpu_mem" // 内存使用量
              await axios.post(queryURL+api,{ "gpu_index":i
              }).then(function (response) {
                self.memData.rows[len - 1]['GPU ' + i.toString()] = Number(response.data['mem_used'])
                // var pieJson = {id:i,pieData:{columns: ['type', 'value'],rows: [{ type: '占比', value: 0 }]}}
              })
              .catch(function (error) {
                console.log(error)
              })

              api = "gpu_bar1mem"
              await axios.post(queryURL+api,{ "gpu_index":i
              }).then(function (response) {
                self.bar1memData.rows[len - 1]['GPU ' + i.toString()] = Number(response.data['mem_used'])
                // var pieJson = {id:i,pieData:{columns: ['type', 'value'],rows: [{ type: '占比', value: 0 }]}}
              })
              .catch(function (error) {
                console.log(error)
              })

              api = "gpu_proc"
              var processes
              await axios.post(queryURL+api,{ "gpu_index":i
              }).then(function (response) {
                proc_num = response.data['proc_counts']
                processes = response.data['processes']
                // var pieJson = {id:i,pieData:{columns: ['type', 'value'],rows: [{ type: '占比', value: 0 }]}}
              })
              .catch(function (error) {
                console.log(error)
              })
              // console.log(proc_num,processes)
              for (var j = 1; j <= proc_num; j++) {
                  var taskJson = {processes}
                  console.log(processes)
                  var _process = processes['proc'+j.toString()]
                  taskJson["pid"] = _process['pid']
                  taskJson['进程名称'] = _process['name']
                  taskJson['内存占用'] = _process['mem_usage']
                  taskJson['设备编号'] = "GPU "+i.toString()
                  tmptableData.push(taskJson)
              }
          }
        }catch(err){
          console.log(err)
        }
        this.tableData = tmptableData
        // console.log(this.tempData.rows)

        // console.log(axisData);
      },
            // 这是一个定时器
      timer() {
          return setInterval(()=>{
              this.getData()
          },this.intervalTime)
    }
  },
  mounted() {
    this.getStaticInfo()

      // console.log("加载完成")
  },
  created() {
      // console.log("创建完成")
      // this.getData()
  },
  activated(){
      // console.log(gupCounts)
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
