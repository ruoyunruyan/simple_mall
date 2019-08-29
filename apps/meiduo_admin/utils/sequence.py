from apps.goods.models import GoodsChannelGroup


def channel_sequence_handler(channel_group_instance, new_sequence=None, old_sequence=None, sequence=0, channel_count=0, add=True):
    """
    抽出方法
    :param channel_group_instance: GoodsChannelGroup 的一个示例对象
    :param new_sequence:  要修改成的序号
    :param old_sequence:  修改前的序号, 存在为修改, 不存在为删除或者新增
    :param sequence: 序号
    :param channel_count:  指定频道组中的频道总数
    :param add: 指定增加还是减少
    :return:
    """
    if new_sequence and old_sequence:
        if new_sequence > old_sequence:
            channels = channel_group_instance.channels.filter(sequence__gt=old_sequence,
                                                              sequence__lte=new_sequence).order_by('sequence')
            for channel in channels:
                channel.sequence -= 1
                channel.save()
        else:
            channels = channel_group_instance.channels.filter(sequence__gte=new_sequence,
                                                              sequence__lt=old_sequence).order_by('sequence')
            for channel in channels:
                channel.sequence += 1
                channel.save()

    if sequence < channel_count:
        if add:
            channels = channel_group_instance.channels.filter(sequence__gte=sequence).order_by('sequence')
            for channel in channels:
                channel.sequence += 1
                channel.save()
        else:
            channels = channel_group_instance.channels.filter(sequence__gt=sequence).order_by('sequence')
            for channel in channels:
                channel.sequence -= 1
                channel.save()
