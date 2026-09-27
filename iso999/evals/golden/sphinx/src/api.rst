API reference
=============

.. py:module:: kelpworks

.. py:function:: dry(frond, *, hours=12)

   Dry a frond.

.. py:function:: dry_all(fronds)

   Dry many fronds.

.. py:function:: dryer()

   Return a dryer.

.. py:class:: Frond(length)

   A frond.

   .. py:method:: __init__(length)
   .. py:method:: __len__()
   .. py:method:: dry()
   .. py:method:: Weigh()
   .. py:method:: rinse()
   .. py:attribute:: colour
   .. py:attribute:: Length

.. py:class:: FrondError

   Raised on bad fronds.

.. py:data:: MAX_FRONDS

   Largest batch.

.. py:data:: max_hours

   Longest drying time.

.. py:function:: _private_helper()

   Internal.

.. py:module:: kelpworks.tide

.. py:function:: height(when)

   Tide height.

.. py:function:: height2(when)

   Tide height, version 2.

.. py:function:: height10(when)

   Tide height, version 10.

.. py:class:: Tide

   .. py:method:: ebb()
   .. py:method:: flow()
