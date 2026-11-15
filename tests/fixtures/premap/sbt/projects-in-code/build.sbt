ThisBuild / scalaVersion := "3.3.4"

lazy val root = (project in file("."))
  .aggregate(LocalProject("core"), LocalProject("api"))
  .settings(name := "shop")
