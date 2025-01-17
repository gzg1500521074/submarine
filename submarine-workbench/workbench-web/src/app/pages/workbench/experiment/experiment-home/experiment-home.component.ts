/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { Component, OnInit, ViewChild } from '@angular/core';
import { ExperimentInfo } from '@submarine/interfaces/experiment-info';
import { ExperimentFormService } from '@submarine/services/experiment.form.service';
import { ExperimentService } from '@submarine/services/experiment.service';
import { NzMessageService } from 'ng-zorro-antd';
import { interval } from 'rxjs';
import { isEqual } from 'lodash';
import { filter, mergeMap, take, tap, timeout, retryWhen } from 'rxjs/operators';
import { ExperimentFormComponent } from './experiment-form/experiment-form.component';

@Component({
  selector: 'app-experiment-home',
  templateUrl: './experiment-home.component.html',
  styleUrls: ['./experiment-home.component.scss'],
})
export class ExperimentHomeComponent implements OnInit {
  /*
  experiment-list property:
    p.s. CheckedList does not need eventListener to update,
    because when we modify the array in child component,
    the modification will be sync to parent.
  */
  experimentList: ExperimentInfo[] = [];
  isListLoading: boolean = true;
  checkedList: boolean[];
  selectAllChecked: boolean = false;
  switchValue: boolean = true;

  // 查询与分页相关
  name: string = '';
  pageNum: number = 1;
  pageSize: number = 10;
  total: number = 0;

  // auto reload
  reloadPeriod: number = 3000; // default 3s
  reloadInterval = interval(this.reloadPeriod);
  reloadSub = null;

  // mlflow
  isMlflowLoading: boolean = true;
  mlflowUrl: string = '';

  // tensorboard
  isTensorboardLoading: boolean = true;
  tensorboardUrl: string = '';

  @ViewChild('form', { static: true }) form: ExperimentFormComponent;

  constructor(
    private experimentService: ExperimentService,
    private experimentFormService: ExperimentFormService,
    private nzMessageService: NzMessageService
  ) {}

  ngOnInit() {
    this.experimentFormService.fetchListService.subscribe(() => {
      this.fetchExperimentList(false, this.name, this.pageNum, this.pageSize);
    });

    this.experimentService.emitInfo(null);
    // this.getTensorboardInfo(1000, 50000);
    // this.getMlflowInfo(1000, 100000);
    this.onSwitchAutoReload();
  }

  ngOnDestroy() {
    if (this.reloadSub) {
      this.reloadSub.unsubscribe();
    }
  }

  // 修改页码事件
  chagePageIndex(index: number): void {
    console.log("index => ", index)
    this.switchValue = false;
    this.onSwitchAutoReload();
    this.fetchExperimentList(false, this.name, index, this.pageSize);
  }

  // 查询
  search(name: string) {
    console.log('name => ', name)

    this.pageNum = 1;
    this.switchValue = false;
    this.onSwitchAutoReload();
    this.fetchExperimentList(false, this.name.trim(), this.pageNum, this.pageSize);
  }

  fetchExperimentList(isAutoReload: boolean, name: string, pageNum: number, pageSize: number) {
    this.experimentService.fetchExperimentList(name, pageNum, pageSize).subscribe(
      (result) => {
        // 总条数
        this.total = result.total;

        this.isListLoading = false;
        // Partial refresh required
        // exists list size
        const currentListSize = this.experimentList.length;
        // The backend returns a real-time list
        const newListSize = result.list.length;
        this.experimentList = result.list;
        const currentTime = new Date();
        // for loop experiment list
        for (let i = 0; i < this.experimentList.length; i++) {
            // Otherwise compare relevant information and update
            const item = this.experimentList[i];

            // cal duration
            if (item.status === 'Succeeded') {
              const finTime = new Date(item.finishedTime);
              let runTime = null;
              if(!item.runningTime) {
                runTime = new Date(item.createdTime);
                item.runningTime = item.createdTime;
              } else {
                runTime = new Date(item.runningTime);
              }

              const result = (finTime.getTime() - runTime.getTime()) / 1000;
              item.duration = this.experimentService.durationHandle(result);
            } else if (item.runningTime) {
              const runTime = item.runningTime ? new Date(item.runningTime) : new Date(item.createdTime);
              const result = (currentTime.getTime() - runTime.getTime()) / 1000;
              item.duration = this.experimentService.durationHandle(result);
            } else {
              const acceptedTime = new Date(item.acceptedTime);
              const result = (currentTime.getTime() - acceptedTime.getTime()) / 1000;
              item.duration = this.experimentService.durationHandle(result);
            }
        }

        if (!isAutoReload) {
          // If it is auto-reloading, we do not want to change the state of checkbox.
          this.checkedList = [];
          for (let i = 0; i < this.experimentList.length; i++) {
            this.checkedList.push(false);
          }
        }
      },
      (error) => {
        console.error(error);
      }
    );
  }

  onDeleteExperiment(id: string, onMessage: boolean) {
    console.log("delete id => ", id, 'onMessage => ', onMessage);
    this.experimentService.deleteExperiment(id).subscribe(
      () => {
        if (onMessage === true) {
          this.nzMessageService.success('Delete Experiment Successfully!');
        }
        this.fetchExperimentList(false, this.name, this.pageNum, this.pageSize);
      },
      (err) => {
        if (onMessage === true) {
          this.nzMessageService.error(err.message);
        }
      }
    );
  }

  deleteExperiments() {
    for (let i = this.checkedList.length - 1; i >= 0; i--) {
      if (this.checkedList[i] === true) {
        this.onDeleteExperiment(this.experimentList[i].experimentId, false);
      }
    }
    this.selectAllChecked = false;
  }

  onInitModal(obj) {
    this.form.initModal(obj.initMode, obj.initFormType, obj.id, obj.spec);
  }

  onSwitchAutoReload() {
    if (this.switchValue) {
      this.reloadSub = this.reloadInterval.subscribe((res) => {
        this.pageNum = 1;
        this.fetchExperimentList(true, this.name, this.pageNum, this.pageSize);
      });
    } else {
      if (this.reloadSub) {
        this.reloadSub.unsubscribe();
      }
    }
  }

  getTensorboardInfo(period: number, due: number) {
    /*
      It will keep polling every ${period} msec, and stop polling whenever
        1. The tensorboard status turns from unavailble to available
        2. It takes over ${due} msec
    */

    interval(period)
      .pipe(
        mergeMap(() => this.experimentService.getTensorboardInfo()), // map interval observable to tensorboardInfo observable
        retryWhen((error) => error), //  retry to get tensorboardInfo
        tap((x) => console.log(x)), // monitoring the process
        filter((res) => res.available), // only emit the success ones
        take(1), // if succeed, stop emitting new value from source observable
        timeout(due) // if timeout, it will throw an error
      )
      .subscribe(
        (res) => {
          this.isTensorboardLoading = !res.available;
          this.tensorboardUrl = res.url;
        },
        (err) => console.log(err)
      );
  }

  getMlflowInfo(period: number, due: number) {
    interval(period)
      .pipe(
        mergeMap(() => this.experimentService.getMlflowInfo()),
        retryWhen((error) => error),
        tap((x) => console.log(x)),
        filter((res) => res.available),
        take(1),
        timeout(due)
      )
      .subscribe(
        (res) => {
          this.isMlflowLoading = !res.available;
          this.mlflowUrl = res.url;
        },
        (err) => console.log(err)
      );
  }
}
