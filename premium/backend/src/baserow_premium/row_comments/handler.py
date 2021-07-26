from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow_premium.row_comments.exceptions import InvalidRowCommentException
from baserow_premium.row_comments.models import RowComment

User = get_user_model()


class RowCommentHandler:
    @staticmethod
    def get_comments(requesting_user: User, table_id: int, row_id: int) -> QuerySet:
        """
        Returns all the row comments for a given row in a table.

        :param requesting_user: The user who is requesting to lookup the row comments.
        :param table_id: The table to find the row in.
        :param row_id: The id of the row to get comments for.
        :return: A queryset of all row comments for that particular row.
        :raises TableDoesNotExist: If the table does not exist.
        :raises RowDoesNotExist: If the row does not exist.
        :raises UserNotInGroup: If the user is not a member of the group that the
            table is in.
        """

        table = TableHandler().get_table(table_id)
        row = RowHandler().get_row(requesting_user, table, row_id)
        return RowComment.objects.filter(table_id=table_id, row_id=row.id).all()

    @staticmethod
    def create_comment(
        requesting_user: User, table_id: int, row_id: int, comment: str
    ) -> RowComment:
        """
        Creates a new row comment on the specified row.

        :param requesting_user: The user who is making the comment.
        :param table_id: The table to find the row in.
        :param row_id: The id of the row to post the comment on.
        :param comment: The comment to post.
        :return: The newly created RowComment instance.
        :raises TableDoesNotExist: If the table does not exist.
        :raises RowDoesNotExist: If the row does not exist.
        :raises UserNotInGroup: If the user is not a member of the group that the
            table is in.
        :raises InvalidRowCommentException: If the comment is blank or None.
        """

        if comment is None or comment == "":
            raise InvalidRowCommentException()

        table = TableHandler().get_table(table_id)
        row = RowHandler().get_row(requesting_user, table, row_id)
        return RowComment.objects.create(
            user=requesting_user, table=table, row_id=row.id, comment=comment
        )
