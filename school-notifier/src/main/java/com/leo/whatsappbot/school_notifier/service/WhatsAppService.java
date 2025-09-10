package com.leo.whatsappbot.school_notifier.service;


import com.leo.whatsappbot.school_notifier.model.Post;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Service
public class WhatsAppService {

    @Value("${whatsapp.phone.number.id}")
    private String phoneNumberId;

    @Value("${whatsapp.access.token}")
    private String accessToken;

    @Value("${whatsapp.destination.number}")
    private String destinationNumber;

    private final RestTemplate restTemplate = new RestTemplate();



    public void sendPostNotification(Post post){
        String url = "https://graph.facebook.com/v22.0/" + phoneNumberId + "/messages";

        String title = post.getTitle() != null && !post.getTitle().isEmpty() ? post.getTitle() : "-";
        String summary = post.getSummary() != null && !post.getSummary().isEmpty() ? post.getSummary() : "-";
        String link = post.getLink() != null && !post.getLink().isEmpty() ? post.getLink() : "-";
        String date = post.getDate() != null && !post.getDate().isEmpty() ? post.getDate() : "-";


        //Montando corpo da requisiçao
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("messaging_product", "whatsapp");
        requestBody.put("to", destinationNumber);
        requestBody.put("type", "template");

        Map<String, Object> template = new HashMap<>();
        template.put("name", "new_post_alert");
        template.put("language", Map.of("code", "pt_BR"));

        Map<String, Object> body = new HashMap<>();
        body.put("type", "body");
        body.put("parameters", new Object[]{
                Map.of("type", "text", "text", title),
                Map.of("type", "text", "text", summary),
                Map.of("type", "text", "text", link),
                Map.of("type", "text", "text", date)
        });

        template.put("components", new Object[]{body});
        requestBody.put("template", template);

        //Headers
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(accessToken);

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        try {
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.POST, entity, String.class);
            System.out.println("Mensagem enviada com sucesso: " + response.getBody());
        } catch (Exception e) {
            System.err.println("Erro ao enviar mensagem WhatsApp: " + e.getMessage());
        }
    }
}
