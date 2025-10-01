package com.leo.whatsappbot.school_notifier.controller;

import com.leo.whatsappbot.school_notifier.service.PostScheduler;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/job")
public class JobController {

    private final PostScheduler scheduler;

    @Value("${app.job.token}")
    private String jobToken;


    public JobController(PostScheduler scheduler){
        this.scheduler = scheduler;
    }

    @GetMapping("/run")
    public ResponseEntity<String> runJob(@RequestParam String token){
        if (!jobToken.equals(token)){
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Token inválido");
        }
        scheduler.checkNewPosts();
        return ResponseEntity.ok("Job executado com sucesso");
    }
}
