package com.agentflow.controller;

import com.agentflow.dto.TaskRequest;
import com.agentflow.dto.TaskResponse;
import com.agentflow.service.TaskService;
import com.agentflow.service.StreamService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import jakarta.validation.Valid;
import java.security.Principal;
import java.util.List;

@RestController
@RequestMapping("/api/tasks")
@RequiredArgsConstructor
public class TaskController {

    private final TaskService taskService;
    private final StreamService streamService;

    @PostMapping
    @ResponseStatus(HttpStatus.ACCEPTED)
    public TaskResponse createTask(
            @Valid @RequestBody TaskRequest request,
            @AuthenticationPrincipal Principal principal) {
        return taskService.createTask(request, principal.getName());
    }

    @GetMapping("/{taskId}")
    public ResponseEntity<TaskResponse> getTask(
            @PathVariable String taskId,
            @AuthenticationPrincipal Principal principal) {
        return taskService.getTask(taskId, principal.getName())
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    public List<TaskResponse> listTasks(@AuthenticationPrincipal Principal principal) {
        return taskService.listTasks(principal.getName());
    }

    @GetMapping(value = "/{taskId}/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamTask(
            @PathVariable String taskId,
            @AuthenticationPrincipal Principal principal) {
        return streamService.createStream(taskId);
    }
}
