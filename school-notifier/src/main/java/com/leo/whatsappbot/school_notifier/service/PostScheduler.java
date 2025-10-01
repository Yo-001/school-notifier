package com.leo.whatsappbot.school_notifier.service;

import com.leo.whatsappbot.school_notifier.model.Post;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.IOException;

import java.util.Optional;

@Component
public class PostScheduler {

    private static Post lastSent = null;

    private final PostScraper scraper;

    private final WhatsAppService whatsappService;


    public PostScheduler(PostScraper scraper, WhatsAppService whatsappService){
        this.scraper = scraper;
        this.whatsappService = whatsappService;
    }

//86_400_000
@Scheduled(fixedRate = 86400000)
    public void checkNewPosts(){

        Optional<Post> optionalPost = scraper.getLastPost();

        if (optionalPost.isPresent()){
            Post newPost = optionalPost.get();


        if (lastSent == null || !lastSent.getLink().equals(newPost.getLink())){
            whatsappService.sendPostNotification(newPost);
            lastSent = newPost;
            System.out.println(newPost);

        }
        }

        System.out.println(lastSent);

    }
}


