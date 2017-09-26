package com.co.etl.shares

import java.io.File

import awscala.sqs.Message
import com.co.etl.{ S3Sink, SqsSource }
import com.co.etl.util.{ TextFileWriter, S3Module, ApplicationProperties, Logging }
import org.joda.time.DateTime

// (1 to 2).par.foreach { _ =>  com.co.etl.shares.ShareMessageCsvSerializer.apply(10) }

object ShareMessageCsvSerializer extends SqsSource
    with Logging
    with S3Sink
    with TextFileWriter
    with ApplicationProperties {
  import properties._

  override def queueName = $("sqs.share.queue")
  override def batchLimit = 10

  final val r = new scala.util.Random

  def apply(num: Int) = {
    val batches = if (num < batchLimit) 1 else 1 + num / batchLimit

    val filename = s"${DateTime.now.toString}-${r.nextInt(Int.MaxValue)}-shares.csv"
    val file = new File(s"/tmp/$filename")
    val uri = S3Module.S3Uri("co-scratch", filename)
    logger.debug(s"${file.getName} created.")

    printToFile(file) { p =>
      for (i <- 1 to batches) {
        logger.debug(s"Serializing batch $i of $batches batches of $num shares.")
        sqs.receiveMessage(queue, batchLimit).foreach { (m: Message) =>
          try {
            import purecsv.safe._
            val share = ShareTransformer.transform(m)._1
            p.println(share.toCSV())
            sqs.delete(m)
          } catch {
            case t: Throwable =>
              logger.debug(s"Unable to write $m due to ${t.getMessage}")
          }
        }
      }
    }

    logger.debug(s"${file.getName} generated.")
    drain { _.put(uri.bucket, uri.key, file) }
    logger.debug(s"${file.getName} uploaded to s3")
    if (file.exists()) file.delete()
  }

}