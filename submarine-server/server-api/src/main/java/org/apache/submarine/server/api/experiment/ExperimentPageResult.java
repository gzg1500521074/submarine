package org.apache.submarine.server.api.experiment;

import java.util.List;

/**
 * @Description
 * @Author guozg
 * @Date 2022/12/10 12:55
 * @Version: 1.0
 */
public class ExperimentPageResult {
  private int pageNum;
  private int pageSize;
  private Long total;
  private List<Experiment> list;

  public ExperimentPageResult(int pageNum, int pageSize, Long total, List<Experiment> list) {
    this.pageNum = pageNum;
    this.pageSize = pageSize;
    this.total = total;
    this.list = list;
  }
}
