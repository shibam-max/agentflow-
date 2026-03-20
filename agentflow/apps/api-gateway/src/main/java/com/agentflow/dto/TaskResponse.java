package com.agentflow.dto;

import lombok.Builder;
import lombok.Data;
import java.time.Instant;

@Data
@Builder
public class TaskResponse {
    private String task_id;
    private String run_id;
    private String status;
    private String stream_url;
    private Float critic_score;
    private Integer revision_count;
    private String final_output;
    private Instant created_at;
}
