package com.co.etl.shares

import awscala.sqs.Message
import com.co.etl._
import com.co.etl.util.Logging

object ShareExtractor extends ShareExtractor

trait ShareExtractor extends Extractor[Int, Message]
    with ShareSqsSource
    with Logging {

  override def extract(batchLimit: Int): Iterator[Message] = {
    val messages = sqs.receiveMessage(queue, batchLimit)
    logger.debug(s"Pulled ${messages.length} messages from $queueName queue for processing")
    messages.iterator
  }
}