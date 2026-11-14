# Reads the repository at ARGV[0] the way github-linguist does, with the gem's own classes, and prints for each
# committed file what the gem says: language, type and the vendored, generated, documentation and binary
# predicates, .gitattributes overrides included. Run by tools/linguist.py beside the CLI.
require 'rugged'
require 'linguist'
require 'json'

repo = Rugged::Repository.new(ARGV[0])
commit = repo.head.target
source = Linguist::Source::RuggedRepository.new(repo)
source.set_attribute_source(commit.oid)
rows = []
commit.tree.walk_blobs(:preorder) do |dir, entry|
  path = dir + entry[:name]
  mode = entry[:filemode].to_s(8)
  next if mode == '120000'
  row = { path: path }
  begin
    blob = Linguist::LazyBlob.new(source, entry[:oid], path, mode)
    lang = blob.language
    row[:language] = lang && lang.name
    row[:type] = lang && lang.type.to_s
    row[:vendored] = !!blob.vendored?
    row[:generated] = !!blob.generated?
    row[:documentation] = !!blob.documentation?
    row[:binary] = !!blob.binary?
    row[:stats] = !!blob.include_in_language_stats?
  rescue StandardError => e
    row[:error] = e.class.name + ': ' + e.message[0, 200]
  end
  rows << row
end
puts JSON.generate(rows)
