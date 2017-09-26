package com.co.etl.shares

import awscala.sqs.Message
import com.co.etl.SqsSource
import com.co.etl.util.{ ApplicationProperties, Logging }

object ShareMessageReplayer extends SqsSource with Logging with ApplicationProperties {
  import properties._
  override def queueName = $("sqs.share.queue") + "-failover"
  override def batchLimit = 10

  def apply(num: Int) = {
    val batches = if (num < batchLimit) 1 else 1 + num / batchLimit
    for (i <- 1 to batches) {
      sqs.receiveMessage(queue, batchLimit).foreach { (m: Message) =>
        sqs.send(ShareExtractor.queue, m.body)
        sqs.delete(m)
      }
    }
  }

}