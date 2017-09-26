package com.co.etl.shares

import slick.driver.PostgresDriver.api._
import slick.profile.SqlAction

trait ShareSql {
  def insertIntoShareLogTable(targetTableName: String, imgId: String, userId: Option[Long], shareType: String, eventDate: String): SqlAction[Int, NoStream, Effect] = {
    sqlu"""
      INSERT INTO #$targetTableName values (
        $imgId,
        $userId,
        $shareType,
        $eventDate,
        default
      );
    """
  }
}
