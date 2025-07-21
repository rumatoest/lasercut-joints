# Inkscape Laser Cut Joints Creator

Plugin idea based on [QuickJoint](https://github.com/JarrettR/QuickJoint.git) which is buggy and thus very annoying to use.
I plan to fix the bugs but IMHO code was so messy that I decided to rewrite it as an new Inkscape plugin.

The core idea of this plugin is to have minimum practical functionality without bugs.

## Описание

Inkscape плагин для создания соединений для лазерной резки.

Как работать с плагином:

 - конвертируете объект в кривые (можно этого не делать, но могут быть глюки)
 - выбираете объект
 - запускаете плагин
 - указываете номер отрезка в кривой на котором нужно создать соединение
 - установите галочку "Live preview", что бы увидеть результат

Плагин будет пытаться обработать отрезки как прямые и выстроит на них соединения.
Для функциональности кривые отрезки тоже обрабатываются как прямые.

Пазы рисуются отдельным объектом, отцентрированным относительно исходного отрезка на котором создаются выступы.

Выступы должны быть комплиментарны к пазам и друг к другу. Если у вас два отрезка одинаковой длинны и на одном у вас 3 выступа от края, а на другом 2 выступа в центре, то они должны соединяться друг с другом.

