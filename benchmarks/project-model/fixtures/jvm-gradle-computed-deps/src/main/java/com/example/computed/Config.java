package com.example.computed;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.dataformat.yaml.YAMLMapper;
import java.io.IOException;

public final class Config {
    @JsonProperty("name")
    public String name;

    @JsonProperty("port")
    public int port;

    public static Config parse(String yaml) throws IOException {
        return new YAMLMapper().readValue(yaml, Config.class);
    }
}
