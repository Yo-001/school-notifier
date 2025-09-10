package com.leo.whatsappbot.school_notifier.controller;

import com.leo.whatsappbot.school_notifier.model.Post;
import com.leo.whatsappbot.school_notifier.repository.PostRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/test")
public class TestController {

    @Autowired
    private PostRepository repo;

    @GetMapping("/posts")
    public List<Post> getAllPosts(){
        return repo.findAll();
    }
}
