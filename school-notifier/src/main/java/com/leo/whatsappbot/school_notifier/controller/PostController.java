package com.leo.whatsappbot.school_notifier.controller;

import com.leo.whatsappbot.school_notifier.model.Post;
import com.leo.whatsappbot.school_notifier.service.PostScraper;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;


@RestController
@RequestMapping("/posts")
public class PostController {

    private final PostScraper postScraper;

    public PostController(PostScraper postScraper){
        this.postScraper = postScraper;
    }

    @GetMapping("/latest")
    public Optional<Post> getLastPost() {
        return postScraper.getLastPost();
    }
}
