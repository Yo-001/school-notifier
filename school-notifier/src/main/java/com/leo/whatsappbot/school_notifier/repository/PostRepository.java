package com.leo.whatsappbot.school_notifier.repository;

import com.leo.whatsappbot.school_notifier.model.Post;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PostRepository extends JpaRepository<Post, Long> {
   boolean existsByTitleAndLink(String title, String link);


}
