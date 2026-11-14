package com.example.ledger.core

import cats.syntax.all.*

final case class Entry(account: String, cents: Long)

object Ledger:
  def balances(entries: List[Entry]): Map[String, Long] =
    entries.foldMap(e => Map(e.account -> e.cents))
