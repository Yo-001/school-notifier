package com.leo.whatsappbot.school_notifier.service;

import com.leo.whatsappbot.school_notifier.model.Post;
import com.leo.whatsappbot.school_notifier.repository.PostRepository;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Component
public class PostScheduler {

    private static final String SITE_URL = "https://www.edu.xunta.gal/centros/ceipxosefernandez/node";

    private final PostScraper scraper;

    private final PostRepository repo;

    private final WhatsAppService whatsappService;


    public PostScheduler(PostScraper scraper, PostRepository repo, WhatsAppService whatsappService){
        this.scraper = scraper;
        this.repo = repo;
        this.whatsappService = whatsappService;
    }
//86_400_000
@Scheduled(fixedRate = 86400000)
    public void checkNewPosts() throws IOException {

    try {
        Document doc = Jsoup.connect(SITE_URL).get();

        // Selects the block from the first post
        Elements posts = doc.select("div.node");

        //Selects the last post
        Element firstPost = posts.get(1);

        String title = firstPost.select("h2.title").text();
        Elements summaryElements = firstPost.select("p:lt(3)");
        String summary = summaryElements.text();
        Elements linkElement = firstPost.select("div.content a:lt(2)");
        List<String> links = new ArrayList<>();
        for (Element linkEl : linkElement) {
            links.add(linkEl.attr("href"));
        }
        String allLinks = String.join(", ", links);
        String date = firstPost.select("span.submitted").text();

        Post entity = new Post();
        entity.setTitle(title);
        entity.setSummary(summary);
        entity.setLink(allLinks);
        entity.setDate(date);

        List<Post> repoObj = repo.findAll();
        List<String> repoTitle = new ArrayList<String>();
        for (Post eTitle : repoObj) {
            repoTitle.add(eTitle.getTitle());
        }
        List<String> repoLink = new ArrayList<String>();
        for (Post eLink : repoObj) {
            repoLink.add(eLink.getLink());
        }

        if (!repoTitle.contains(title) && !repoLink.contains(allLinks)) {
                Post saved = repo.save(entity);
                whatsappService.sendPostNotification(saved);
                System.out.println(repoTitle);
                System.out.println(saved);
        } else {
            System.out.println(repoTitle);
            System.out.println("Post duplicado, nada foi adicionado ao repo!");
        }

    } catch (IOException e) {
        throw new RuntimeException("Erro ao acessar o site: " + SITE_URL, e);
    }
}
}

