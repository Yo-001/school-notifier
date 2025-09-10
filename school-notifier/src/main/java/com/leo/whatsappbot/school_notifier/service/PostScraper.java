package com.leo.whatsappbot.school_notifier.service;

import com.leo.whatsappbot.school_notifier.model.Post;
import com.leo.whatsappbot.school_notifier.repository.PostRepository;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

@Service
public class PostScraper {

    private static final String SITE_URL = "https://www.edu.xunta.gal/centros/ceipxosefernandez/node";

    private final PostRepository repo;

    public PostScraper(PostRepository repo){
        this.repo = repo;
    }

            public  Optional<Post> getLastPost() {

                try {
                    // Connects and download the page's HTML
                    Document doc = Jsoup.connect(SITE_URL).get();

                // Selects the block from the first post
                Elements posts = doc.select("div.node");
                if (posts.isEmpty()) {
                    return Optional.empty();
                }
                    //Selects the last post
                    Element firstPost = posts.get(1);

                    //Gets the data
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

                    // Montar entity Post
                    Post entity = new Post();
                    entity.setTitle(title);
                    entity.setSummary(summary);
                    entity.setLink(allLinks);
                    entity.setDate(date);

                    //Checks and saves the entity
                    return repo.existsByTitleAndLink(entity.getTitle(), entity.getLink())
                            ? Optional.empty()
                            : Optional.of(repo.save(entity));
        } catch (IOException e) {
            throw new RuntimeException("Erro ao acessar o site: " + SITE_URL, e);
        }
                
    }
}
