
(define (problem aladdin-story-problem)
  (:domain aladdin-story)

  (:objects
   ;; the stage
   castle - place
   mountain - place
   ;; the props
   lamp - magic-lamp
   big-treasure - thing
   small-treasure - thing
   )

  (:init
   ;; initial (dynamic) state
   (alive aladdin)
   (at aladdin castle)
   (single aladdin)
   (unconfined aladdin)
   (alive jafar)
   (at jafar castle)
   (single jafar)
   (unconfined jafar)
   (has jafar small-treasure)
   (values-more-than jafar big-treasure small-treasure)
   (values-more-than jafar small-treasure lamp)
   (alive jasmine)
   (at jasmine castle)
   (single jasmine)
   (unconfined jasmine)
   (alive dragon)
   (at dragon mountain)
   (unconfined dragon)
   (has dragon lamp)
   (has dragon big-treasure)
   (values-more-than dragon big-treasure small-treasure)
   (values-more-than dragon small-treasure lamp)
   (alive gene)
   (in gene lamp)

   ;; some static facts
   (scary dragon)
   (scary gene)
   (beautiful jasmine)
   (loyal-to jafar aladdin)
   (single dragon)
   (single gene)

   )

  (:goal
   (and
      (exists (?c1 - character ?c2 - character) (married-to ?c2 ?c1))
   )
   )
  )
