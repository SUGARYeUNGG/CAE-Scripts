    //
    using System;
    using System.Collections.Generic;

    using System.Linq;
    // 提供在AutoCAD中创建命令方法和处理运行时行为的API。
    using Autodesk.AutoCAD.Runtime;
    // 管理应用程序相关的服务，比如访问活动文档。
    using Autodesk.AutoCAD.ApplicationServices;
    // 提供处理AutoCAD数据库的类，用于管理图纸、块、实体等。
    using Autodesk.AutoCAD.DatabaseServices;
    using Autodesk.AutoCAD.EditorInput;
    using Autodesk.Civil.ApplicationServices;
    using Autodesk.AutoCAD.Geometry;




[assembly: CommandClass(typeof(EntityCreate.AlphaShapes))]
[assembly: CommandClass(typeof(EntityCreate.Program))]



namespace EntityCreate
{


    public class AlphaShapes
    {

        public static List<Point> ConcaveHull(List<Point> dataset, int k)
        {
            var hull = new List<Point>();
            var firstPoint = FindMinYPoint(dataset);
            hull.Add(firstPoint);
            var currentPoint = firstPoint;
            dataset.Remove(currentPoint);

            double prevAngle = 0;
            while (true)
            {
                var nearestNeighbours = NearestNeighbours(dataset, currentPoint, k);
                var sortedByAngle = SortByAngle(nearestNeighbours, currentPoint, prevAngle);

                bool found = false;
                for (int i = 0; i < sortedByAngle.Count; i++)
                {
                    var candidate = sortedByAngle[i];

                    // 增加检查：新点与现有的多段线是否相交
                    if (!IntersectsWithHull(hull, candidate))
                    {
                        currentPoint = candidate;
                        hull.Add(currentPoint);
                        dataset.Remove(currentPoint);
                        prevAngle = Angle(hull[hull.Count - 2], hull[hull.Count - 1]);
                        found = true;
                        break;
                    }
                }

                // 如果没有找到合适的点，或者已经回到起点，结束循环
                if (!found || PointsEqual(currentPoint, firstPoint))
                    break;
            }

            return hull;
        }


        // Find the k-nearest neighbours of point p in dataset
        public static List<Point> NearestNeighbours(List<Point> dataset, Point p, int k)
        {
            return dataset.OrderBy(point => Distance(p, point)).Take(k).ToList();
        }

        // Sort points based on angle relative to the previous point
        // Sort points based on angle relative to the previous point
        public static List<Point> SortByAngle(List<Point> points, Point from, double prevAngle)
        {
            return points.OrderBy(p => NormalizeAngle(Angle(from, p) - prevAngle)).ToList();
        }


        // Calculate the angle between two points
        public static double Angle(Point a, Point b)
        {
            return Math.Atan2(b.y - a.y, b.x - a.x);
        }

        // Normalize angle to 0 <= angle < 2*PI
        public static double NormalizeAngle(double radians)
        {
            if (radians < 0) return radians + 2 * Math.PI;
            return radians;
        }

        // Calculate Euclidean distance between two points
        public static double Distance(Point a, Point b)
        {
            return Math.Sqrt(Math.Pow(a.x, 2) + Math.Pow(a.y, 2));
        }

        // Check if two points are equal
        public static bool PointsEqual(Point a, Point b)
        {
            return a.x == b.x && a.y == b.y;
        }

        // Check if the line (a->b) intersects with any line segment in the hull


        // 检查是否与当前多段线的任何线段相交
        public static bool IntersectsWithHull(List<Point> hull, Point newPoint)
        {
            for (int i = 0; i < hull.Count - 1; i++)
            {
                if (Intersects(hull[i], hull[i + 1], hull[hull.Count - 1], newPoint))
                    return true;
            }
            return false;
        }

        // Determine if two line segments (p1->p2 and p3->p4) intersect
        public static bool Intersects(Point p1, Point p2, Point p3, Point p4)
        {
            // Line segment intersection logic
            // Adapted from geometric intersection principles
            double d1 = Direction(p3, p4, p1);
            double d2 = Direction(p3, p4, p2);
            double d3 = Direction(p1, p2, p3);
            double d4 = Direction(p1, p2, p4);

            return (((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) &&
                    ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0)));
        }

        // Helper for intersection detection
        public static double Direction(Point pi, Point pj, Point pk)
        {
            return (pk.x - pi.x) * (pj.y - pi.y) - (pj.x - pi.x) * (pk.y - pi.y);
        }

        // Find the point with the minimum y-coordinate (or leftmost in case of tie)
        public static Point FindMinYPoint(List<Point> points)
        {
            return points.OrderBy(p => p.y).ThenBy(p => p.x).First();
        }
    }

    public static class Program
    {


        [CommandMethod("AlphaShapes")]
        public static void RunAlphaShapes()
        {
            // 获取当前文档和数据库
            Document doc = Application.DocumentManager.MdiActiveDocument;
            Database db = doc.Database;
            Editor ed = doc.Editor;
            CivilDocument civilDoc = CivilApplication.ActiveDocument;
            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                BlockTable blockTable = tr.GetObject(db.BlockTableId, OpenMode.ForRead) as BlockTable;
                BlockTableRecord blockTableRecord = tr.GetObject(blockTable[BlockTableRecord.ModelSpace], OpenMode.ForWrite) as BlockTableRecord;


                List<Point> points = new List<Point>
                {
                new Point(1, 1),
                new Point(2, 5),
                new Point(4, 3),
                new Point(6, 6),
                new Point(5, 2),
                new Point(3, 3),
                new Point(7, 8),
                new Point(9, 5),
                new Point(11, 3),
                new Point(13, 7),
                new Point(10, 2),
                new Point(8, 4),
                new Point(12, 6),
                new Point(14, 1),
                new Point(15, 5),
                new Point(16, 3),
                new Point(18, 6),
                new Point(17, 2),
                new Point(19, 4),
                new Point(20, 7),
                new Point(21, 1),
                new Point(22, 5),
                new Point(23, 3),
                new Point(24, 6),
                new Point(25, 2),
                new Point(26, 4)
                };
                ed.WriteMessage("原始点集中点的数量：{0}\n", points.Count);

                // k 是一个关键参数，用于控制凹壳计算过程中每一步选择的最近邻居的数量。
                // 通过调整 k 的值，可以影响凹壳的形状和细节程度。
                int k = 5;
                var hull = AlphaShapes.ConcaveHull(points, k);

                // 在模型空间中将点表示出来

                // 将points中的点也在模型空间中表示出来
                foreach (var p in points)
                {
                    DBPoint dbPoint = new DBPoint(new Autodesk.AutoCAD.Geometry.Point3d(p.x, p.y, 0));
                    blockTableRecord.AppendEntity(dbPoint);
                    tr.AddNewlyCreatedDBObject(dbPoint, true);
                }
                ed.WriteMessage("hull中点的数量：{0}\n", hull.Count);
                ed.WriteMessage("Concave Hull Points:\n");
                foreach (var p in hull)
                {
                    ed.WriteMessage("坐标:({0},{1})\n", p.x, p.y);
                    DBPoint dbPoint = new DBPoint(new Autodesk.AutoCAD.Geometry.Point3d(p.x, p.y, 0));
                    blockTableRecord.AppendEntity(dbPoint);
                    tr.AddNewlyCreatedDBObject(dbPoint, true);
                }
                // 创建Polyline并连接hull中的点

                ConvexHull(hull);


                // 创建 Polyline
                using (Polyline polyline = new Polyline())
                {
                    polyline.ColorIndex = 1;
                    polyline.LineWeight = LineWeight.LineWeight030;

                    for (int i = 0; i < hull.Count; i++)
                    {
                        Point point = hull[i];
                        polyline.AddVertexAt(i, new Point2d(point.x, point.y), 0, 0, 0);
                    }

                    // 如果需要将起点和终点相连，形成闭合 Polyline
                    polyline.Closed = true;

                    // 将 Polyline 添加到模型空间
                    blockTableRecord.AppendEntity(polyline);
                    tr.AddNewlyCreatedDBObject(polyline, true);
                }


                // 打开线宽
                // 打开线宽显示
                Application.SetSystemVariable("LWDISPLAY", 1);


                tr.Commit();
            }
        }




        static Document _doc = Application.DocumentManager.MdiActiveDocument;
        static Editor _editor = _doc.Editor;



        public static void ConvexHull(List<Point> points)
        {
            Document doc = Application.DocumentManager.MdiActiveDocument;
            Database db = doc.Database;
            Editor ed = doc.Editor;
            CivilDocument civilDoc = CivilApplication.ActiveDocument;

            List<Point> prehull = new List<Point>(points);


            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                DocumentLock docLock = doc.LockDocument();   // 解决使用按钮时 eLockViolation 错误

                BlockTable blockTable = tr.GetObject(db.BlockTableId, OpenMode.ForRead) as BlockTable;
                BlockTableRecord blockTableRecord = tr.GetObject(blockTable[BlockTableRecord.ModelSpace], OpenMode.ForWrite) as BlockTableRecord;

                // 在模型空间中将点表示出来
                foreach (var p in prehull)
                {
                    DBPoint dbPoint = new DBPoint(new Autodesk.AutoCAD.Geometry.Point3d(p.x, p.y, 0));
                    blockTableRecord.AppendEntity(dbPoint);
                    tr.AddNewlyCreatedDBObject(dbPoint, true);
                }



                // 计算凸包
                int n = prehull.Count;
                List<Point> hull = ClassConvexHull.convexHull(prehull, n);

                // 创建 Polyline 并连接 hull 中的点
                using (Polyline ConvexBorder = new Polyline())
                {
                    for (int i = 0; i < hull.Count; i++)
                    {
                        ConvexBorder.AddVertexAt(i, new Point2d(hull[i].x, hull[i].y), 0, 0, 0);
                    }

                    ConvexBorder.Closed = true;
                    ConvexBorder.Color = Autodesk.AutoCAD.Colors.Color.FromRgb(255, 0, 0);
                    ConvexBorder.LineWeight = LineWeight.LineWeight030;

                    blockTableRecord.AppendEntity(ConvexBorder);
                    tr.AddNewlyCreatedDBObject(ConvexBorder, true);
                }

                tr.Commit();
            }

            // 打开线宽显示
            Autodesk.AutoCAD.ApplicationServices.Application.SetSystemVariable("LWDISPLAY", 1);

            // Update the display and diaplay a message box
            // doc.Editor.Regen();
            //Autodesk.AutoCAD.ApplicationServices.Application.ShowAlertDialog("处理完毕 !");
        }





    }


}
