| Откуда             | Куда               | Тип Django          | Почему                                                                                                         |
| ------------------ | ------------------ | ------------------- | -------------------------------------------------------------------------------------------------------------- |
| User               | TeacherProfile     | OneToOneField       | Один профиль педагога на один аккаунт                                                                          |
| User               | StudentProfile     | OneToOneField       | Один профиль ученика на один аккаунт                                                                           |
| TeacherProfile     | TeachingAssignment | ForeignKey          | Один педагог ведет много учеников                                                                              |
| StudentProfile     | TeachingAssignment | ForeignKey          | Один ученик занимается у нескольких педагогов                                                                  |
| Subject            | TeachingAssignment | ForeignKey          | Один предмет изучают многие ученики                                                                            |
| MusicPiece         | Category           | ManyToManyField     | Одно произведение может относиться к нескольким категориям, а каждая категория содержит множество произведений |
| MusicPiece         | MusicMaterial      | ForeignKey          | У произведения много материалов                                                                                |
| TeachingAssignment | Performance        | ForeignKey          | Одно обучение включает много исполнений                                                                        |
| MusicPiece         | Performance        | ForeignKey          | Одно произведение исполняют многие ученики                                                                     |
| Performance        | PerformanceComment | ForeignKey          | У исполнения много комментариев                                                                                |
| User               | PerformanceComment | ForeignKey          | Один пользователь пишет много комментариев                                                                     |
| User               | Article            | ForeignKey          | Один автор создает много статей                                                                                |



