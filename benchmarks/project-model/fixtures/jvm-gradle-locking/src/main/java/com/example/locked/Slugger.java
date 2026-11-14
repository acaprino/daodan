package com.example.locked;

import java.util.Locale;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class Slugger {
    private static final Logger LOG = LoggerFactory.getLogger(Slugger.class);

    public String slug(String title) {
        String slug = StringUtils.stripAccents(title).trim().toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", "-");
        LOG.debug("slug({}) = {}", title, slug);
        return slug;
    }
}
