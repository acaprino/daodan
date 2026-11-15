import sbt._

// a plugin of the build adds the modules: no `lazy val` of build.sbt names them
object Modules extends AutoPlugin {
  override def trigger = allRequirements
  val core = Project("core", file("modules/core"))
  val api = Project("api", file("modules/api")).dependsOn(core)
  override def extraProjects = Seq(core, api)
}
