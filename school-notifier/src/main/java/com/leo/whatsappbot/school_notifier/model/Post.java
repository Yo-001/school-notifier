package com.leo.whatsappbot.school_notifier.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "posts")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Post {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;


    @Column(unique = true)
    private String title;

    @Column(unique = true, length = 500)
    private String link;

    @Column(length = 500)
    private String summary;

    private String date;
}
